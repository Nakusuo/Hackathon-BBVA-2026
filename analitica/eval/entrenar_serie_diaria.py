"""Entrena, valida y guarda la serie diaria del pronostico de saldo (30 dias con banda al 80 %).
Validacion con el mismo corte temporal con embargo que el modelo de 30 dias (prueba: 2024 a 2025, que el modelo no vio al entrenar), dia por dia y contra dos lineas base.
Uso: python analitica/eval/entrenar_serie_diaria.py   ->  models/serie_diaria.pkl y models/metricas_serie_diaria.json"""
import json
import os
import sys
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "backend"))
warnings.filterwarnings("ignore")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.comun.rutas import DATA_GENERADO, MODELOS  # noqa: E402
from src.models import datos, pronostico as P, serie_diaria as SD  # noqa: E402

CORTES = {"entrena_hasta": "2023-06-30", "calibra_desde": "2023-10-01", "prueba_desde": "2024-01-01"}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def resumen_dias(tab: pd.DataFrame) -> dict:
    return {"cobertura_media": float(tab["cobertura_80"].mean()), "cobertura_minima": float(tab["cobertura_80"].min()), "cobertura_maxima": float(tab["cobertura_80"].max()),
            "mae_rel_medio": float(tab["mae_rel_ingreso"].mean()), "ancho_rel_medio": float(tab["ancho_rel"].mean())}


def main():
    t0 = time.time()
    seg = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))["asignacion_entrenamiento"]
    pk = joblib.load(os.path.join(MODELOS, "pronostico.pkl"))
    F, params = pk["features"], pk["params"]
    s, cl, ctx = datos.cargar_series(DATA_GENERADO), datos.cargar_clientes(DATA_GENERADO), datos.cargar_contexto(DATA_GENERADO)
    df = P.construir_origenes(s, cl, ctx, seg)
    C = P.cortes(df, CORTES)
    ent, aj, cal, te = C["entrena"], C["ajusta"], C["calibra"], C["prueba"]
    log(f"origenes {len(df):,} (entrena {len(ent):,}, ajusta {len(aj):,}, calibra {len(cal):,}, prueba {len(te):,})")

    # --- fase de evaluacion: todo ajustado SIN mirar la ventana de prueba
    m30 = P.Pronosticador(F, params=params, por_segmento=True).ajustar(ent, aj, cal)
    log(f"modelo de 30 dias de la fase de evaluacion listo ({time.time() - t0:.0f}s)")
    serie = SD.SerieDiaria(m30, F, params).ajustar(ent, aj, cal)
    log(f"cuantiles de {len(SD.ANCLAS)} horizontes y recalibracion por dia listos ({time.time() - t0:.0f}s)")
    pred = serie.predecir(te)
    tab = SD.metricas_por_dia(te, pred)
    p30 = m30.predecir(te)
    lin = SD.metricas_por_dia(te, SD.linea_base_lineal(te, p30))
    ma3 = SD.metricas_por_dia(te, SD.linea_base_ma3(te, SD.cuantiles_residuo_ma3(cal)))
    ancla = list(SD.ANCLAS) + [SD.H]
    en_ancla, fuera = tab.loc[ancla], tab.drop(index=ancla)
    # el dia 30 es la salida del modelo de 30 dias: el esperado es identico; la banda solo cambia donde los cuantiles se cruzaban (bajo > esperado) y se ensancha hasta el esperado
    banda_igual = np.isclose(pred["bajo"][:, -1], p30["saldo_bajo"].to_numpy()) & np.isclose(pred["alto"][:, -1], p30["saldo_alto"].to_numpy())
    coincide_dia30 = {"esperado_identico": bool(np.allclose(pred["esperado"][:, -1], p30["saldo_esperado"].to_numpy())), "fraccion_con_banda_corregida": float(1 - banda_igual.mean()),
                      "banda_nunca_se_estrecha": bool((pred["bajo"][:, -1] <= p30["saldo_bajo"].to_numpy() + 1e-6).all() and (pred["alto"][:, -1] >= p30["saldo_alto"].to_numpy() - 1e-6).all())}
    # equidad: cobertura por tipo de trabajo en tres dias
    attr = cl.reindex(s.ids[te["cliente_idx"].to_numpy()])
    por_tipo = {}
    for tipo in attr["tipo_trabajo"].unique():
        m = (attr["tipo_trabajo"] == tipo).to_numpy()
        sub = te[m]
        pt = {k: v[m] for k, v in pred.items()}
        t = SD.metricas_por_dia(sub, pt)
        por_tipo[str(tipo)] = {f"dia_{d}": {"cobertura_80": float(t.loc[d, "cobertura_80"]), "mae_rel_ingreso": float(t.loc[d, "mae_rel_ingreso"])} for d in (7, 15, 30)} | {"n": int(m.sum())}
    R = {"horizontes_entrenados": list(SD.ANCLAS) + [SD.H], "origenes": {"entrena": len(ent), "ajusta": len(aj), "calibra": len(cal), "prueba": len(te)}, "cortes": CORTES,
         "serie_diaria": resumen_dias(tab), "en_horizontes_entrenados": resumen_dias(en_ancla), "en_dias_intermedios_no_entrenados": resumen_dias(fuera),
         "linea_base_recta_al_dia_30": resumen_dias(lin), "linea_base_promedio_movil_3_meses": resumen_dias(ma3), "ultimo_punto_coincide_con_el_modelo_de_30_dias": coincide_dia30,
         "por_dia": {"serie_diaria": tab.round(5).reset_index().to_dict("records"), "recta_al_dia_30": lin.round(5).reset_index().to_dict("records"), "promedio_movil_3_meses": ma3.round(5).reset_index().to_dict("records")},
         "por_tipo_de_trabajo": por_tipo}
    with open(os.path.join(MODELOS, "metricas_serie_diaria.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    log(f"validacion: cobertura media {R['serie_diaria']['cobertura_media']:.3f} (min {R['serie_diaria']['cobertura_minima']:.3f}, max {R['serie_diaria']['cobertura_maxima']:.3f}); "
        f"error {R['serie_diaria']['mae_rel_medio']:.3f} frente a {R['linea_base_recta_al_dia_30']['mae_rel_medio']:.3f} (recta) y {R['linea_base_promedio_movil_3_meses']['mae_rel_medio']:.3f} (promedio movil)")

    # --- modelo final: igual que el de 30 dias, con todos los origenes de objetivo conocido y la calibracion de los ultimos 3 meses
    corte = df["fecha"].max() - pd.Timedelta(days=90)
    ent_f = df[df["fecha"] < corte - pd.Timedelta(days=30) - pd.Timedelta(days=60)]
    aj_f = df[(df["fecha"] >= corte - pd.Timedelta(days=90)) & (df["fecha"] < corte - pd.Timedelta(days=30))]
    cal_f = df[df["fecha"] >= corte]
    final = SD.SerieDiaria(pk["modelo"], F, params).ajustar(ent_f, aj_f, cal_f)
    P.guardar({"modelo": final, "features": F, "horizontes": list(SD.ANCLAS) + [SD.H], "datos_hasta": str(df["fecha"].max().date()), "metricas_prueba": R["serie_diaria"]}, "serie_diaria")
    log(f"serie diaria final guardada ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
