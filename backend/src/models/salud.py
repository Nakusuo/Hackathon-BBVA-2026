"""Salud financiera 0 a 100: puntaje transparente con componentes visibles, especializado por tipo de trabajo.
Un ingreso irregular no se mide con la vara de uno fijo: al independiente se le pide más colchón, se le pesa menos la variación del ingreso (es parte de su trabajo)
y se mide cuantos meses malos aguanta."""
import numpy as np
import pandas as pd

# componente: (columna, valor_malo, valor_bueno). Entre malo y bueno el puntaje es lineal; fuera se recorta a 0 o 100.
BASE = {
    "colchon": ("colchon_observado", 0.0, 3.0),
    "deuda": ("cuota_sobre_ingreso", 0.40, 0.05),
    "gastos_fijos": ("fijo_sobre_ingreso", 0.70, 0.30),
    "estabilidad_ingreso": ("cv_ingreso", 0.80, 0.10),
    "ahorro": ("ahorro_pct", 0.0, 0.15),
    "tension_de_caja": ("dias_rojo_3m", 15.0, 0.0),
    "resiliencia": ("meses_malos_que_aguanta", 0.0, 8.0),   # colchon / variacion del ingreso: cuantos meses de caida tipica cubre
}
# Pesos por familia. Suman 1. El dependiente no usa resiliencia; el independiente pide mas colchon (4,5 meses) y pesa menos la estabilidad.
PESOS = {
    "dependiente": {"colchon": 0.25, "deuda": 0.20, "gastos_fijos": 0.15, "estabilidad_ingreso": 0.15, "ahorro": 0.15, "tension_de_caja": 0.10, "resiliencia": 0.0},
    "independiente": {"colchon": 0.20, "deuda": 0.15, "gastos_fijos": 0.15, "estabilidad_ingreso": 0.05, "ahorro": 0.15, "tension_de_caja": 0.15, "resiliencia": 0.15},
}
COLCHON_BUENO = {"dependiente": 3.0, "independiente": 4.5}
FAMILIA = {"dependiente": "dependiente", "dependiente_con_comision": "dependiente", "independiente": "independiente", "mixto": "independiente"}
EXPLICACION = {
    "colchon": "tu colchón (meses de ingreso disponibles)", "deuda": "el peso de tus cuotas sobre tu ingreso", "gastos_fijos": "la parte de tu ingreso que ya esta comprometida en gastos fijos",
    "estabilidad_ingreso": "que tan parejo es tu ingreso de un mes a otro", "ahorro": "cuanto apartas de lo que ganas", "tension_de_caja": "los días en que tu saldo quedo en rojo",
    "resiliencia": "cuantos meses malos de ingreso podrías aguantar con tu colchón",
}


def _tramo(x, malo, bueno):
    return 100 * np.clip((np.asarray(x, dtype=float) - malo) / (bueno - malo), 0, 1)


def _preparar(f: pd.DataFrame) -> pd.DataFrame:
    g = f.copy()
    g["meses_malos_que_aguanta"] = g["colchon_observado"] / np.maximum(g["cv_ingreso"], 0.2)
    return g


def familia_de(f: pd.DataFrame) -> pd.Series:
    if "tipo_trabajo" not in f:
        return pd.Series("dependiente", index=f.index)
    return f["tipo_trabajo"].map(FAMILIA).fillna("dependiente")


def componentes(f: pd.DataFrame) -> pd.DataFrame:
    g, fam = _preparar(f), familia_de(f)
    out = {}
    for k, (c, malo, bueno) in BASE.items():
        if k == "colchon":
            bueno_v = fam.map(COLCHON_BUENO).to_numpy()
            out[k] = 100 * np.clip((g[c].to_numpy(dtype=float) - malo) / (bueno_v - malo), 0, 1)
        else:
            out[k] = _tramo(g[c], malo, bueno)
    return pd.DataFrame(out, index=f.index)


def pesos_de(f: pd.DataFrame) -> pd.DataFrame:
    fam = familia_de(f)
    return pd.DataFrame([PESOS[x] for x in fam], index=f.index)


def puntaje_salud(f: pd.DataFrame) -> pd.Series:
    return (componentes(f) * pesos_de(f)).sum(axis=1).rename("salud")


def puntaje_generico(f: pd.DataFrame) -> pd.Series:
    """El puntaje sin especializar (pesos del dependiente para todos). Solo para comparar en la validacion."""
    pesos = pd.Series(PESOS["dependiente"])
    g, comp = _preparar(f), {}
    for k, (c, malo, bueno) in BASE.items():
        comp[k] = _tramo(g[c], malo, bueno)
    return (pd.DataFrame(comp, index=f.index) * pesos).sum(axis=1).rename("salud_generica")


def explicar(fila: pd.Series, n: int = 2) -> list[dict]:
    """Los n componentes qué más restan: (peso x lo que falta para 100)."""
    f1 = fila.to_frame().T
    comp = componentes(f1).iloc[0]
    pesos = pesos_de(f1).iloc[0]
    resta = {k: (100 - comp[k]) * pesos[k] for k in comp.index if pesos[k] > 0}
    peores = sorted(resta, key=resta.get, reverse=True)[:n]
    return [{"componente": k, "puntaje": round(float(comp[k]), 1), "peso": float(pesos[k]), "puntos_que_resta": round(resta[k], 1), "que_mide": EXPLICACION[k]} for k in peores]
