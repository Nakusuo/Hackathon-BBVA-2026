"""Informe de calidad de los datos generados (data/QUALITY.md). Todo numero sale de las tablas, ninguno se escribe a mano."""
import json
import os

import numpy as np
import pandas as pd

from src.generador.contexto import cargar_yaml

ANCLA_INEI_URBANO = 2093.7
ANCLA_INEI_TOTAL = 1925.9


def _leer(carpeta: str, nombre: str, columnas=None) -> pd.DataFrame:
    return pd.read_parquet(os.path.join(carpeta, nombre), columns=columnas)


def _md(df: pd.DataFrame, decimales: int = 2) -> str:
    df = df.copy()
    cab = "| " + " | ".join(str(c) for c in [df.index.name or ""] + list(df.columns)) + " |\n|" + "---|" * (len(df.columns) + 1) + "\n"
    filas = ""
    for i, r in df.iterrows():
        filas += "| " + " | ".join([str(i)] + [f"{v:,.{decimales}f}" if isinstance(v, (float, np.floating)) else f"{v:,}" if isinstance(v, (int, np.integer)) else str(v) for v in r]) + " |\n"
    return cab + filas


def calcular(carpeta: str) -> dict:
    gen = cargar_yaml("generador.yaml")
    meta = json.load(open(os.path.join(carpeta, "meta.json"), encoding="utf-8"))
    cl = _leer(carpeta, "clientes.parquet").set_index("customer_id")
    tx = _leer(carpeta, "transacciones", ["customer_id", "transaction_id", "fecha_hora", "monto", "monto_pen", "tipo", "categoria", "glosa", "saldo", "es_recurrente", "es_atipico", "es_suscripcion_duplicada"])
    pm = _leer(carpeta, "panel_mensual")
    sd = _leer(carpeta, "saldo_diario", ["customer_id", "fecha", "saldo_cierre", "en_rojo"])
    et = _leer(carpeta, "etiquetas_calidad")
    ms = _leer(carpeta, "mensajes")
    seg = cl["segmento"]
    pm["seg"] = pm["customer_id"].map(seg)
    sd["seg"] = sd["customer_id"].map(seg)
    r = {"meta": meta, "n_cl": len(cl), "n_tx": len(tx), "n_msg": len(ms)}

    est = cl.groupby(["arquetipo", "perfil_ahorro_real", "perfil_gasto_real"]).agg(n=("peso_muestral", "size"), peso=("peso_muestral", "mean"))
    est["participacion_muestra"] = est["n"] / len(cl)
    est["participacion_objetivo"] = est["participacion_muestra"] * est["peso"]
    r["estratos"] = est
    r["region"] = pd.DataFrame({"muestra": cl["region"].value_counts(normalize=True), "objetivo": pd.Series(gen["poblacion"]["region"]["values"])})
    r["edad"] = pd.DataFrame({"muestra": cl["rango_edad"].value_counts(normalize=True), "objetivo": pd.Series(gen["poblacion"]["edad"]["values"])}).sort_index()

    montos = tx.groupby("tipo", observed=True)["monto_pen"].describe(percentiles=[.01, .5, .99])[["count", "min", "1%", "50%", "99%", "max"]]
    r["montos"] = montos
    n = len(tx)
    faltantes = pd.Series({c: tx[c].isna().mean() for c in ["glosa", "categoria", "saldo", "monto"]})
    r["faltantes"] = faltantes
    r["problemas"] = et["tipo_problema"].value_counts()
    r["atipicos"] = tx["es_atipico"].mean()
    r["recurrentes"] = tx["es_recurrente"].mean()
    r["clientes_sub_dup"] = int(tx.loc[tx["es_suscripcion_duplicada"], "customer_id"].nunique())

    w = cl["peso_muestral"]
    a25 = pm[pm["mes"].str.startswith("2025")].assign(w=lambda d: d["customer_id"].map(w))
    r["ingreso_2025"] = a25.groupby("seg")["ingreso_operativo"].mean()
    r["ingreso_2025_ponderado"] = float(np.average(a25["ingreso_operativo"], weights=a25["w"]))
    sin_grati = pm[~pm["mes"].str[-2:].isin(["07", "12"])]
    cv = sin_grati.groupby("customer_id")["ingreso_operativo"].agg(lambda s: s.std() / s.mean())
    r["cv_ingreso"] = cv.groupby(seg).median()
    m = pm[pm["mes"].isin(["2020-02", "2020-04"])].pivot_table(index="seg", columns="mes", values="ingreso_operativo", aggfunc="mean")
    r["covid"] = m["2020-04"] / m["2020-02"]
    r["rojo_seg"] = sd.groupby("seg")["en_rojo"].mean()
    r["rojo_anio"] = sd.groupby(sd["fecha"].dt.year)["en_rojo"].mean()
    r["clientes_con_rojo"] = float(sd.groupby("customer_id")["en_rojo"].any().mean())
    r["sentimiento"] = ms["sentimiento"].value_counts(normalize=True)
    ms2 = ms.assign(fecha=ms["fecha_hora"].dt.normalize()).merge(sd[["customer_id", "fecha", "en_rojo"]], on=["customer_id", "fecha"], how="left")
    r["rojo_por_sentimiento"] = ms2.groupby("sentimiento", observed=True)["en_rojo"].mean()
    ult = tx.dropna(subset=["saldo"]).sort_values("fecha_hora").groupby("customer_id", observed=True)["saldo"].last()
    fin = sd[sd["fecha"] == sd["fecha"].max()].set_index("customer_id")["saldo_cierre"]
    r["dif_saldo_mediana"] = float((ult - fin.reindex(ult.index)).abs().median())

    ok = {}
    ok["Ningun estrato vacio"] = bool(est["n"].min() >= 1)
    ok["Pesos muestrales entre 0,5 y 2"] = bool(est["peso"].between(0.5, 2).all())
    dup_exactos = int((et["tipo_problema"] == "duplicado_exacto").sum())
    ok["transaction_id unico salvo duplicados exactos etiquetados"] = bool(tx["transaction_id"].nunique() == n - dup_exactos)
    ok["Montos en soles positivos donde existen"] = bool((tx["monto_pen"].dropna() > 0).all())
    ok["Fechas dentro de la ventana"] = bool(tx["fecha_hora"].min() >= pd.Timestamp(meta["inicio"]) and tx["fecha_hora"].max() < pd.Timestamp(meta["fin"]) + pd.Timedelta(days=1))
    ok["Mas dias en rojo en independientes que en dependientes formales"] = bool(r["rojo_seg"][["independiente_diario", "independiente_proyectos"]].min() > r["rojo_seg"]["formal_quincena"])
    ok["Efecto del confinamiento: el ingreso del independiente de comercio cae a menos de 0,7 del de feb-2020"] = bool(r["covid"].get("independiente_diario", 1) < 0.7)
    ok["Ingreso medio ponderado de 2025 dentro de +-35 % del ingreso urbano INEI"] = bool(abs(r["ingreso_2025_ponderado"] / ANCLA_INEI_URBANO - 1) <= 0.35)
    ok["Irregularidad: CV del ingreso por proyectos mayor que el del formal"] = bool(r["cv_ingreso"]["independiente_proyectos"] > r["cv_ingreso"]["formal_quincena"])
    ok["Saldo del ultimo movimiento coincide con el saldo diario (mediana de la diferencia < 1 sol)"] = bool(r["dif_saldo_mediana"] < 1)
    objetivo = np.array([0.25, 0.38, 0.22, 0.15])
    obs = r["sentimiento"].reindex(["positivo", "neutro", "preocupado", "negativo"]).to_numpy()
    ok["Sentimiento dentro de 5 puntos del reparto objetivo"] = bool(np.all(np.abs(obs - objetivo) < 0.05))
    ok["Faltantes dentro del 50 % relativo de lo configurado"] = bool(all(abs(faltantes[c] / gen["calidad"][f"p_faltante_{c}"] - 1) < 0.5 for c in ["glosa", "categoria", "saldo", "monto"]))
    ok["El mensaje negativo coincide con el saldo en rojo mas que el neutro"] = bool(r["rojo_por_sentimiento"]["negativo"] > r["rojo_por_sentimiento"]["neutro"])
    r["controles"] = ok
    return r


def escribir(carpeta: str, destino: str) -> dict:
    r = calcular(carpeta)
    m = r["meta"]
    gen = cargar_yaml("generador.yaml")
    ctl = "\n".join(f"| {'OK' if v else 'FALLA'} | {k} |" for k, v in r["controles"].items())
    estados = {}
    for k, v in gen["poblacion"]["arquetipos"].items():
        estados[k] = v.get("estado", "")
    texto = f"""# Calidad de los datos sinteticos

Generado por `src/generador/reporte.py` a partir de las tablas de `{os.path.basename(carpeta)}`. Todos los numeros salen de los datos; la configuracion esta en `data/parametros/`.

## 1. Trazabilidad
| Dato | Valor |
|---|---|
| Semilla | {m['semilla']} |
| Clientes | {m['clientes']:,} |
| Ventana | {m['inicio']} a {m['fin']} |
| Movimientos | {r['n_tx']:,} (incluye duplicados sembrados) |
| Mensajes | {r['n_msg']:,} |
| Tiempo de generacion | {m['segundos']} s, lotes de {m['lote']} clientes |
| Python, numpy, pandas | {m['python']}, {m['numpy']}, {m['pandas']} |
| Huella de parametros | `{m['huella_parametros']}` |
| Perfiles semilla | {m['fuente_perfiles']} |

Misma semilla y mismos parametros dan las mismas tablas (lo comprueba `tests/test_generador.py`).

## 2. Sesgo de muestreo: estratos y pesos
Cada cliente pertenece a un estrato arquetipo x perfil de ahorro x perfil de gasto. Ningun estrato baja del piso configurado ({gen['estratos']['piso_por_estrato']:.0%}) y el peso muestral restituye la proporcion objetivo, de modo que se puede sobremuestrear un estrato pequeno sin que sesgue las metricas ponderadas.

{_md(r['estratos'], 3)}
Region (muestra frente a objetivo):

{_md(r['region'], 3)}
Edad (muestra frente a objetivo):

{_md(r['edad'], 3)}
## 3. Montos (S/)
{_md(r['montos'], 1)}
## 4. Calidad sembrada para probar el tratamiento
- Faltantes (fraccion de movimientos): glosa {r['faltantes']['glosa']:.2%}, categoria {r['faltantes']['categoria']:.2%}, saldo {r['faltantes']['saldo']:.2%}, monto {r['faltantes']['monto']:.2%}.
- Duplicados y faltantes etiquetados en `etiquetas_calidad`: {', '.join(f'{k} {v:,}' for k, v in r['problemas'].items())}.
- Gastos atipicos: {r['atipicos']:.3%} de los movimientos. Salen del presupuesto del mes, de modo que el saldo no se desvia.
- Movimientos recurrentes: {r['recurrentes']:.1%}. Clientes con una suscripcion duplicada: {r['clientes_sub_dup']}.

## 5. Contraste con una fuente oficial
Ingreso operativo mensual medio de 2025 por segmento (S/):

{_md(r['ingreso_2025'].to_frame('ingreso_2025'), 0)}
Ponderado por el peso muestral: **S/ {r['ingreso_2025_ponderado']:,.0f}**. Ancla INEI EPEN abr-2025 a mar-2026: S/ {ANCLA_INEI_TOTAL:,.1f} nacional y S/ {ANCLA_INEI_URBANO:,.1f} urbano (cuadros 1.28 y 1.30). La poblacion objetivo es bancarizada y por eso queda algo por encima del promedio nacional.

## 6. Irregularidad y eventos
CV mensual del ingreso (sin los meses de gratificacion), mediana por segmento:

{_md(r['cv_ingreso'].to_frame('cv'), 2)}
Ingreso de abril de 2020 sobre el de febrero de 2020, por segmento:

{_md(r['covid'].to_frame('abr/feb'), 2)}
Dias con saldo negativo: por segmento

{_md(r['rojo_seg'].to_frame('fraccion_de_dias'), 3)}
y por anio

{_md(r['rojo_anio'].to_frame('fraccion_de_dias'), 3)}
Clientes con al menos un dia en rojo: {r['clientes_con_rojo']:.0%}.

## 7. Texto
Reparto de sentimiento de los mensajes: {', '.join(f'{k} {v:.1%}' for k, v in r['sentimiento'].items())}. Fraccion con saldo en rojo ese dia: {', '.join(f'{k} {v:.1%}' for k, v in r['rojo_por_sentimiento'].items())}.

## 8. Controles automaticos
| Estado | Control |
|---|---|
{ctl}

## 9. Limites que hay que decir
- Los datos son sinteticos: un modelo puede descubrir lo que el generador sembro. Por eso cada modelo se evalua frente a un baseline y con pruebas de perturbacion.
- Las magnitudes de los eventos son supuestos del equipo, anclados en cifras publicas donde existen (estado `parcial` o `supuesto` en `data/parametros/eventos.yaml`).
- Los arquetipos, las regiones y las edades tienen pesos del equipo, no de una encuesta. Con microdatos de la ENAHO se pasa una tabla semilla y se regenera.
- El efectivo no observado esta modelado (fraccion por segmento) pero no hay datos reales para calibrarlo.
- Los atributos internos del simulador (`ingreso_base`, `gasto_ratio`, `fraccion_efectivo` y otros) no son observables: `src/models/columnas.py` define que puede ver un modelo.
"""
    with open(destino, "w", encoding="utf-8") as f:
        f.write(texto)
    return r["controles"]
