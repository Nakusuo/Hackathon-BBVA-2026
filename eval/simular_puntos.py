"""Simula la economia del programa de puntos con los movimientos reales de 2025. Uso: python eval/simular_puntos.py -> models/metricas_programa_puntos.json"""
import json
import os
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.comun.rutas import DATA_GENERADO, MODELOS  # noqa: E402
from src.models import datos, niveles as N, programa_puntos as PP, salud as SA, segmentacion as S  # noqa: E402


def construir_tabla() -> pd.DataFrame:
    cl = datos.cargar_clientes(DATA_GENERADO)
    seg = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))
    f = S.features_cliente(DATA_GENERADO, "2026-01-01")
    lab = pd.Series(S.asignar(seg, f), index=f.index)
    salud = SA.puntaje_salud(f)
    nivel = pd.Series([N.nivel_individual(seg["niveles"][int(l)], float(salud[c])) for c, l in lab.items()], index=f.index)
    tx = datos.cargar_transacciones(DATA_GENERADO, ["customer_id", "fecha_hora", "tipo", "canal", "monto_pen", "transaction_id"], desde="2025-01-01", hasta="2026-01-01")
    tx = tx[~tx["transaction_id"].astype(str).str.endswith("D")].drop_duplicates("transaction_id")
    canales = PP.cfg()["programa"]["supuestos_economicos"]["canales_que_pagan_comision"]
    gasto_elegible = tx[(tx["tipo"].astype(str) == "gasto") & (tx["canal"].astype(str).isin(canales))].groupby("customer_id")["monto_pen"].sum() / 12
    panel = datos.cargar_panel(DATA_GENERADO)
    p25 = panel[panel["mes"].str.startswith("2025")]
    ahorro = p25.groupby("customer_id")["ahorro_movido"].mean()
    aporte = p25.assign(a=p25["ahorro_movido"] > 0).groupby("customer_id")["a"].mean()
    sd = datos.cargar_series(DATA_GENERADO)
    fechas = sd.fechas
    en25 = (fechas >= "2025-01-01") & (fechas < "2026-01-01")
    rojo = (sd.saldo[:, en25] < 0)
    dias = fechas[en25]
    quincena = np.where(dias.day <= 15, 0, 1) + 2 * (dias.month - 1)
    sin_rojo = np.stack([~rojo[:, quincena == q].any(axis=1) for q in range(24)], axis=1).sum(axis=1) / 12
    df = pd.DataFrame({"nivel": nivel, "consumo_elegible": gasto_elegible.reindex(f.index).fillna(0), "ahorro_apartado": ahorro.reindex(f.index).fillna(0), "dias_rojo_3m": f["dias_rojo_3m"],
                       "quincenas_sin_rojo": pd.Series(sin_rojo, index=sd.ids).reindex(f.index), "meses_con_aporte": aporte.reindex(f.index).fillna(0)})
    return df, cl["peso_muestral"].reindex(f.index)


if __name__ == "__main__":
    df, peso = construir_tabla()
    r = PP.economia(df, peso)
    r["topes_de_reinversion"] = PP.verificar_topes()
    r["niveles_de_la_muestra"] = df["nivel"].value_counts().to_dict()
    json.dump(r, open(os.path.join(MODELOS, "metricas_programa_puntos.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    t = r["total"]
    print("topes (costo/comision por consumo, debe ser <= 0,30):", {k: round(v, 3) for k, v in r["topes_de_reinversion"].items()})
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items()})
    print(pd.DataFrame(r["por_nivel"]).T.round(2).to_string())
