"""Entrena y evalua todos los modelos con los datos finales y guarda los .pkl y models/metricas.json.
Uso: python eval/entrenar_modelos.py [--etapas segmentacion pronostico clasificacion impacto]"""
import argparse
import json
import os
import sys
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.comun.rutas import DATA_GENERADO, MODELOS  # noqa: E402
from src.models import clasificacion as KL, datos, equidad as EQ, impacto as IM, niveles as N, pronostico as P, pronostico_mensual as PM, riesgo_clima as RC, salud as SA, segmentacion as S  # noqa: E402

CORTES = {"entrena_hasta": "2023-06-30", "calibra_desde": "2023-10-01", "prueba_desde": "2024-01-01"}
METRICAS = os.path.join(MODELOS, "metricas.json")


def _json(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, (pd.DataFrame, pd.Series)):
        return json.loads(o.to_json(orient="index" if isinstance(o, pd.DataFrame) else None))
    if isinstance(o, dict):
        return {str(k): _json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json(v) for v in o]
    return o


def guardar_metricas(clave: str, valor) -> None:
    """Un archivo por etapa (models/metricas_<etapa>.json): las etapas pueden correr en procesos distintos sin pisarse."""
    os.makedirs(MODELOS, exist_ok=True)
    json.dump(_json(valor), open(os.path.join(MODELOS, f"metricas_{clave}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def etapa_segmentacion():
    t = time.time()
    m = S.entrenar(DATA_GENERADO, "2023-07-01")
    f, lab, prep = m["features"], m["etiquetas"], m["prep"]
    niveles = N.nombres_por_segmento(f, lab)
    cl = datos.cargar_clientes(DATA_GENERADO)
    D = S.distancia_gower(prep.numericas(f), f[S.CATEGORICAS].to_numpy(dtype=object))
    from sklearn.metrics import silhouette_score
    km, reg = S.baseline_kmeans(prep, f, m["k"]), S.baseline_reglas(f)
    desc = m["descripcion"].copy()
    desc["nivel"] = desc.index.map(niveles)
    desc["salud_mediana"] = SA.puntaje_salud(f).groupby(lab).median().round(1)
    comp = f.assign(seg=lab, nivel=[niveles[x] for x in lab]).join(cl[["region", "rango_edad", "departamento", "arquetipo"]], rsuffix="_cl")
    equidad = {g: comp.groupby(g)["nivel"].value_counts(normalize=True).unstack(fill_value=0).round(3) for g in ("region", "rango_edad", "arquetipo")}
    res = {"k": m["k"], "tabla_k": m["tabla_k"], "silueta_gower": {"kprototypes": float(silhouette_score(D, lab, metric="precomputed")), "kmeans_onehot": float(silhouette_score(D, km, metric="precomputed")),
                                                                    "reglas_2x2": float(silhouette_score(D, reg, metric="precomputed"))},
           "ari_vs_etiquetas": S.comparar_con_etiquetas({"kprototypes": lab, "kmeans_onehot": km, "reglas_2x2": reg}, cl, f.index), "descripcion": desc.drop(columns=["tipo_trabajo_frecuente"], errors="ignore"),
           "arranque_en_frio_precision": m["frio_acc"], "referencia_clase_mayoritaria": float(np.bincount(lab).max() / len(lab)), "composicion_de_niveles_por_grupo": equidad, "niveles": niveles}
    guardar_metricas("segmentacion", res)
    g = {k: v for k, v in m.items() if k not in ("features", "etiquetas")}
    g.update({"niveles": niveles, "asignacion_entrenamiento": dict(zip(f.index, lab.tolist()))})
    S.guardar(g)
    log(f"segmentacion lista k={m['k']} niveles={niveles} ({time.time() - t:.0f}s)")
    return g


def etapa_pronostico():
    t = time.time()
    seg = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))
    seg_map = seg["asignacion_entrenamiento"]
    s, cl, ctx = datos.cargar_series(DATA_GENERADO), datos.cargar_clientes(DATA_GENERADO), datos.cargar_contexto(DATA_GENERADO)
    df = P.construir_origenes(s, cl, ctx, seg_map)
    C = P.cortes(df, CORTES)
    ent, aj, cal, te = C["entrena"], C["ajusta"], C["calibra"], C["prueba"]
    F = P.FEATURES_BASE + ["segmento"]
    pesos = cl["peso_muestral"].reindex(s.ids).to_numpy()
    te = te.assign(peso=pesos[te["cliente_idx"].to_numpy()])
    R = {"origenes": {k: len(v) for k, v in C.items()}, "cortes": CORTES}
    log(f"origenes {len(df):,}; optimizando")
    mej = P.optimizar(ent, aj, F, n_trials=25, timeout=300)
    params = {k: v for k, v in mej.items() if not k.startswith("_")}
    R["optuna"] = mej
    modelo = P.Pronosticador(F, params=params, por_segmento=True).ajustar(ent, aj, cal)
    pr = modelo.predecir(te)
    cuant_ma, cuant_st = P.cuantiles_residuo(cal, "net_ma3"), P.cuantiles_residuo(cal, "st_net")
    R["saldo_30d"] = {"ma3_baseline_plan": P.metricas(te, P.baseline_ma3(te, cuant_ma)), "perfil_estructural": P.metricas(te, P.baseline_estructural(te, cuant_st)), "lightgbm_optimizado": P.metricas(te, pr)}
    # pesos muestrales: la misma metrica ponderada por la poblacion objetivo
    w = te["peso"]
    err = lambda p: float(np.average((p["saldo_esperado"] - te["y_saldo"]).abs() / te["escala"], weights=w))  # noqa: E731
    R["mae_rel_ponderado"] = {"ma3": err(P.baseline_ma3(te, cuant_ma)), "lightgbm": err(pr)}
    ant = (te["saldo_t"] > 0).to_numpy()
    y = te["rojo30"].to_numpy()
    R["rojo_30d_anticipacion"] = {"lightgbm_calibrado": P.metricas_rojo(y[ant], pr["p_rojo"].to_numpy()[ant]), "saldo_bajo_regla": P.metricas_rojo(y[ant], (1 / (1 + np.exp(te["saldo_rel"].to_numpy() * 3)))[ant]),
                                  "perfil_estructural": P.metricas_rojo(y[ant], (1 / (1 + np.exp(te["st_min_rel"].to_numpy() * 3)))[ant]), "tasa_positivos": float(y[ant].mean()), "n": int(ant.sum())}
    net = (te["net_ma3"] * te["escala"]).to_numpy()
    ruta_ma = te["saldo_t"].to_numpy()[:, None] + np.arange(1, 31)[None, :] * net[:, None] / 30
    lin = np.where((ruta_ma < 0).any(1), (ruta_ma < 0).argmax(1) + 1, 31)
    R["dia_de_riesgo"] = {"lightgbm": P.dia_de_riesgo_aciertos(te[ant], pr["dia_riesgo"].to_numpy()[ant]), "estructural": P.dia_de_riesgo_aciertos(te[ant], te["st_dia"].to_numpy()[ant]),
                          "ma_lineal": P.dia_de_riesgo_aciertos(te[ant], lin[ant])}
    # equidad: error y cobertura por grupo
    ids = s.ids[te["cliente_idx"].to_numpy()]
    attr = cl.reindex(ids)
    expo = pd.Series([RC.exposicion_fen(d)["nivel"] for d in attr["departamento"]], index=te.index)
    grupos = {"segmento": te["segmento"].astype(int).astype(str), "region": pd.Series(attr["region"].to_numpy(), index=te.index), "rango_edad": pd.Series(attr["rango_edad"].to_numpy(), index=te.index),
              "tipo_trabajo": pd.Series(attr["tipo_trabajo"].to_numpy(), index=te.index), "exposicion_fen": expo, "arquetipo": pd.Series(attr["arquetipo"].to_numpy(), index=te.index)}
    eq = {}
    for g, serie in grupos.items():
        tabla = EQ.por_grupo(te, pr, serie, te["peso"])
        eq[g] = {"tabla": tabla, "brechas": EQ.brechas(tabla)}
    R["equidad_por_grupo"] = eq
    log("equidad lista; remuestreo del riesgo de rojo")
    R["remuestreo_rojo"] = EQ.comparar_remuestreo(ent, cal, te, F)
    # perturbaciones
    rng = np.random.default_rng(1)
    ruido = te.copy()
    for c in ("ing30", "ing60", "ing90", "gas30", "gas60", "gas90"):
        ruido[c] = ruido[c] * rng.lognormal(0, 0.10, len(ruido))
    falt = te.copy()
    for c in F[:-1]:
        falt.loc[rng.random(len(falt)) < 0.2, c] = np.nan
    cp = cl.reindex(s.ids)["cambio_patron"].to_numpy()[te["cliente_idx"].to_numpy()]
    R["perturbaciones"] = {"original": P.metricas(te, pr), "ruido_10pct_en_historial": P.metricas(ruido, modelo.predecir(ruido)), "faltantes_extra_20pct": P.metricas(falt, modelo.predecir(falt)),
                           "clientes_con_cambio_de_patron": P.metricas(te[cp], pr[cp]), "clientes_sin_cambio_de_patron": P.metricas(te[~cp], pr[~cp])}
    # evento no visto: dejar el confinamiento fuera del entrenamiento
    f = df["fecha"]
    ev_ini, ev_fin = pd.Timestamp("2020-03-01"), pd.Timestamp("2021-09-30")
    en_ev = (f >= ev_ini) & (f <= ev_fin)
    ent_e = df[(f < pd.Timestamp("2023-06-01")) & ~((f >= ev_ini - pd.Timedelta(days=30)) & (f <= ev_fin + pd.Timedelta(days=30)))]
    aj_e = df[(f >= pd.Timestamp("2023-06-01")) & (f < pd.Timestamp("2023-09-01"))]
    cal_e = df[(f >= pd.Timestamp("2023-09-01")) & (f < pd.Timestamp("2023-12-01"))]
    te_ev = df[en_ev]
    cm = P.cuantiles_residuo(cal_e, "net_ma3")
    res_ev = {"n_origenes_en_evento": len(te_ev), "ma3": P.metricas(te_ev, P.baseline_ma3(te_ev, cm))}
    for nombre, feats in (("lightgbm_sin_variables_de_evento", F), ("lightgbm_con_evento_actual", F + ["ev_ahora"]), ("lightgbm_con_escenario_conocido", F + ["ev_ahora", "ev_horizonte"])):
        mm = P.Pronosticador(feats, params=params, por_segmento=True).ajustar(ent_e, aj_e, cal_e)
        res_ev[nombre] = P.metricas(te_ev, mm.predecir(te_ev))
    R["evento_no_visto_confinamiento"] = res_ev
    log("evento no visto listo; ablacion de texto")
    # texto: ¿los mensajes ayudan? sentimiento PREDICHO, nunca la etiqueta
    ms = pd.read_parquet(os.path.join(DATA_GENERADO, "mensajes"))
    ms["customer_id"] = ms["customer_id"].astype(str)
    sn = KL.entrenar_sentimiento(ms)
    colt = KL.columnas_texto(df, s.ids, s.fechas, ms, sn["modelo"])
    df2 = pd.concat([df, colt], axis=1)
    C2 = P.cortes(df2, CORTES)
    Ft = F + list(colt.columns)
    mt = P.Pronosticador(Ft, params=params, por_segmento=True).ajustar(C2["entrena"], C2["ajusta"], C2["calibra"])
    pt = mt.predecir(C2["prueba"])
    a2 = (C2["prueba"]["saldo_t"] > 0).to_numpy()
    base_mae = np.abs(pr["saldo_esperado"] - te["y_saldo"]).to_numpy() / te["escala"].to_numpy()
    txt_mae = np.abs(pt["saldo_esperado"] - C2["prueba"]["y_saldo"]).to_numpy() / C2["prueba"]["escala"].to_numpy()
    cli = te["cliente_idx"].to_numpy()
    dif = pd.Series(base_mae - txt_mae).groupby(cli).mean()
    boots = [dif.sample(len(dif), replace=True, random_state=i).mean() for i in range(400)]
    R["texto_en_el_pronostico"] = {"sin_texto": P.metricas(te, pr), "con_texto": P.metricas(C2["prueba"], pt), "rojo_pr_auc_sin": R["rojo_30d_anticipacion"]["lightgbm_calibrado"]["pr_auc"],
                                   "rojo_pr_auc_con": P.metricas_rojo(y[a2], pt["p_rojo"].to_numpy()[a2])["pr_auc"], "mejora_mae_rel": {"media": float(dif.mean()), "ic95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}}
    guardar_metricas("pronostico", R)
    # modelo final: todos los origenes con objetivo conocido; conformal con los ultimos 3 meses
    corte_cal = df["fecha"].max() - pd.Timedelta(days=90)
    ent_f = df[df["fecha"] < corte_cal - pd.Timedelta(days=30) - pd.Timedelta(days=60)]
    aj_f = df[(df["fecha"] >= corte_cal - pd.Timedelta(days=90)) & (df["fecha"] < corte_cal - pd.Timedelta(days=30))]
    cal_f = df[df["fecha"] >= corte_cal]
    final = P.Pronosticador(F, params=params, por_segmento=True).ajustar(ent_f, aj_f, cal_f)
    P.guardar({"modelo": final, "features": F, "params": params, "datos_hasta": str(df["fecha"].max().date()), "metricas_prueba": R["saldo_30d"]["lightgbm_optimizado"]}, "pronostico")
    joblib.dump({"modelo": sn["modelo"], "resultados": sn["resultados"]}, os.path.join(MODELOS, "sentimiento.pkl"), compress=3)
    log(f"pronostico listo ({time.time() - t:.0f}s)")


def etapa_clasificacion():
    t = time.time()
    cols = ["customer_id", "transaction_id", "fecha_hora", "monto", "monto_pen", "tipo", "categoria", "comercio", "glosa", "canal", "es_recurrente", "es_atipico", "es_suscripcion_duplicada"]
    tx = datos.cargar_transacciones(DATA_GENERADO, cols)
    log(f"transacciones {len(tx):,}")
    g = KL.entrenar_glosa(tx)
    R = {"glosa_a_categoria": g["resultados"]}
    joblib.dump({"modelo": g["modelo"], "resultados": g["resultados"]}, os.path.join(MODELOS, "glosa.pkl"), compress=3)
    log("glosa lista")
    ids = sorted(tx["customer_id"].unique())[:150]
    s = tx[tx["customer_id"].isin(ids)].dropna(subset=["monto"]).copy()
    pr, bl = KL.detectar_recurrentes(s), KL.baseline_mismo_comercio(s)
    y = s["es_recurrente"].astype(int)
    dup = KL.detectar_suscripciones_duplicadas(s)
    real = set(s.loc[s["es_suscripcion_duplicada"], "customer_id"].astype(str))
    todos = set(map(str, ids))
    R["recurrentes"] = {"periodicidad_y_monto": KL.prf(y, pr.astype(int)), "baseline_mismo_comercio_3_veces": KL.prf(y, bl.astype(int)), "n_clientes": len(ids)}
    R["suscripciones_duplicadas"] = {**KL.prf([c in real for c in todos], [c in dup for c in todos]), "detectados": len(dup), "reales": len(real)}
    R["atipicos"] = KL.evaluar_atipicos(tx[tx["customer_id"].isin(sorted(tx["customer_id"].unique())[:200])])
    ms = pd.read_parquet(os.path.join(DATA_GENERADO, "mensajes"))
    R["sentimiento"] = KL.entrenar_sentimiento(ms)["resultados"]
    guardar_metricas("clasificacion", R)
    log(f"clasificacion lista ({time.time() - t:.0f}s)")


def etapa_mensual():
    t = time.time()
    seg_map = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))["asignacion_entrenamiento"]
    cl = datos.cargar_clientes(DATA_GENERADO)
    df = PM.construir_filas(DATA_GENERADO, cl, seg_map)
    C = PM.cortes(df)
    m = PM.Mensual().ajustar(C["entrena"], C["ajusta"], C["calibra"])
    te = C["prueba"]
    ids = np.array(sorted(cl.index))
    attr = cl.reindex(ids)
    te = te.assign(tipo=attr["tipo_trabajo"].to_numpy()[te["cliente_idx"].to_numpy()], reg_txt=attr["region"].to_numpy()[te["cliente_idx"].to_numpy()],
                   edad_txt=attr["rango_edad"].to_numpy()[te["cliente_idx"].to_numpy()], seg=te["segmento"].astype(int).astype(str))
    fijo, rec, bl = m.predecir(te), m.predecir_recalibrado(df, te), PM.baselines(te, C["calibra"])
    cols = ["ing_mae_rel", "ing_wape", "ing_cobertura", "gas_mae_rel", "gas_wape", "gas_cobertura", "net_mae_rel", "net_cobertura"]
    R = {"ventanas": {k: {"filas": len(v), "origen_desde": str(v["fecha_origen"].min().date()), "origen_hasta": str(v["fecha_origen"].max().date())} for k, v in C.items()},
         "por_horizonte": {"lightgbm_recalibracion_continua": PM.metricas(te, rec)[cols], "lightgbm_conformal_fijo": PM.metricas(te, fijo)[cols], "mismo_mes_anio_previo": PM.metricas(te, bl["mismo_mes_anio_previo"])[cols],
                           "promedio_3_meses": PM.metricas(te, bl["promedio_3_meses"])[cols]}}
    for g, nom in (("tipo", "tipo"), ("seg", "seg"), ("reg_txt", "region"), ("edad_txt", "edad")):
        R[f"por_{nom}"] = {"lightgbm_recalibracion_continua": PM.metricas(te, rec, por=g)[["n", "ing_mae_rel", "ing_cobertura", "gas_mae_rel", "gas_cobertura", "net_cobertura"]],
                         "mismo_mes_anio_previo": PM.metricas(te, bl["mismo_mes_anio_previo"], por=g)[["ing_mae_rel", "ing_cobertura", "gas_mae_rel", "gas_cobertura"]]}
    guardar_metricas("pronostico_mensual", R)
    f = df["fecha_origen"]
    final = PM.Mensual().ajustar(df[f <= "2024-03-31"], df[(f >= "2024-04-01") & (f <= "2024-09-30")], df[(f >= "2024-10-01") & (f <= "2025-05-31")])
    joblib.dump({"modelo": final, "features": PM.FEATURES, "datos_hasta": str(df["fecha_origen"].max().date())}, os.path.join(MODELOS, "pronostico_mensual.pkl"), compress=3)
    log(f"mensual listo ({time.time() - t:.0f}s)")


def etapa_impacto():
    t = time.time()
    seg = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))
    pk = joblib.load(os.path.join(MODELOS, "pronostico.pkl"))
    s, cl, ctx = datos.cargar_series(DATA_GENERADO), datos.cargar_clientes(DATA_GENERADO), datos.cargar_contexto(DATA_GENERADO)
    df = P.construir_origenes(s, cl, ctx, seg["asignacion_entrenamiento"])
    C = P.cortes(df, CORTES)
    # el aviso anticipado usa un modelo entrenado solo con datos anteriores al periodo evaluado (sin fuga)
    mod = P.Pronosticador(pk["features"], params=pk["params"], por_segmento=True).ajustar(C["entrena"], C["ajusta"], C["calibra"])
    te = C["prueba"]
    alerta = pd.DataFrame({"cliente_idx": te["cliente_idx"].to_numpy(), "dia_idx": te["dia_idx"].to_numpy(), "p_rojo": mod.predecir(te)["p_rojo"].to_numpy()})
    f = S.features_cliente(DATA_GENERADO, "2024-01-01")
    tx = datos.cargar_transacciones(DATA_GENERADO, ["customer_id", "transaction_id", "fecha_hora", "categoria", "monto_pen", "es_suscripcion_duplicada"], desde="2024-01-01")
    r = IM.simular(s, cl, f, tx, "2024-01-01", "2025-12-31", origenes_alerta=alerta)
    guardar_metricas("impacto", {"tabla": r["tabla"], "diferencias": r["diferencias"], "por_segmento": r["por_segmento"], "supuestos": r["supuestos"], "meses": r["meses"]})
    log(f"impacto listo ({time.time() - t:.0f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapas", nargs="+", default=["segmentacion", "pronostico", "clasificacion", "impacto"])
    a = ap.parse_args()
    for e in a.etapas:
        log(f"== {e} ==")
        {"segmentacion": etapa_segmentacion, "pronostico": etapa_pronostico, "clasificacion": etapa_clasificacion, "mensual": etapa_mensual, "impacto": etapa_impacto}[e]()
    log("terminado")
