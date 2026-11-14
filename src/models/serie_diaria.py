"""Serie diaria del pronostico de saldo: los 30 dias con banda al 80 %, que es lo que pide el contrato de la API (forecast[]).
El modelo de 30 dias ya estaba validado; aqui se entrenan los mismos cuantiles (10, 50, 90) en los horizontes ANCLAS, se interpola entre ellos y la banda se
RECALIBRA DIA POR DIA con datos de calibracion (conformal), de modo que la cobertura se mide y se asegura en cada uno de los 30 dias, no solo en los horizontes entrenados.
El dia 30 es exactamente la salida del modelo de 30 dias: el ultimo punto de la serie coincide con lo ya validado."""
import numpy as np
import pandas as pd

from src.models import pronostico as P

H = P.H
ANCLAS = (5, 10, 15, 20, 25)   # horizontes entrenados ademas del dia 30
PUNTOS = (0,) + ANCLAS + (H,)   # nodos de la interpolacion (el dia 0 es el saldo de hoy: sin incertidumbre)


def objetivo(h: int) -> str:
    return f"y_net_n_h{h}"


class SerieDiaria:
    def __init__(self, modelo30: "P.Pronosticador", features: list, params: dict, alfa: float = 0.2):
        self.modelo30, self.features, self.params, self.alfa = modelo30, list(features), params, alfa

    # ------------------------------------------------------------------ entrenamiento
    def ajustar(self, ent: pd.DataFrame, aj: pd.DataFrame, cal: pd.DataFrame) -> "SerieDiaria":
        F = self.features
        self.modelos = {h: {a: P.entrenar_cuantil(ent[F], ent[objetivo(h)], a, self.params, aj[F], aj[objetivo(h)]) for a in (0.1, 0.5, 0.9)} for h in ANCLAS}
        lo, mid, hi = self._interpolar(cal)
        self.q_global, self.q_seg = {}, {}
        for d in range(1, H):   # el dia 30 conserva la calibracion del modelo de 30 dias
            y = cal[objetivo(d)].to_numpy()
            e = np.maximum(lo[:, d] - y, y - hi[:, d])
            self.q_global[d] = self._conformal(e)
            self.q_seg[d] = {int(s): self._conformal(e[(cal["segmento"] == s).to_numpy()]) for s in cal["segmento"].unique() if (cal["segmento"] == s).sum() >= 200}
        return self

    def _conformal(self, e: np.ndarray) -> float:
        n = len(e)
        return float(np.quantile(e, min(np.ceil((n + 1) * (1 - self.alfa)) / n, 1.0)))

    # ------------------------------------------------------------------ prediccion
    def _anclas(self, df: pd.DataFrame) -> dict:
        """Cuantiles crudos (sin conformal) en cada nodo, en unidades normalizadas por la escala del cliente. Se ordenan por fila para que lo <= mid <= hi."""
        X = df[self.features]
        n = len(df)
        a = {0: np.zeros((n, 3))}
        for h in ANCLAS:
            a[h] = np.sort(np.column_stack([self.modelos[h][q].predict(X) for q in (0.1, 0.5, 0.9)]), axis=1)
        m30 = self.modelo30.modelos
        a[H] = np.sort(np.column_stack([m30[q].predict(X) for q in (0.1, 0.5, 0.9)]), axis=1)
        return a

    def _interpolar(self, df: pd.DataFrame) -> tuple:
        """Interpolacion lineal entre nodos: (lo, mid, hi) con forma (n, 31); la columna d es el dia d."""
        a = self._anclas(df)
        dias = np.arange(0, H + 1)
        sal = [np.stack([np.interp(dias, PUNTOS, [a[p][i, k] for p in PUNTOS]) for i in range(len(df))]) for k in range(3)]
        return sal[0], sal[1], sal[2]

    def predecir(self, df: pd.DataFrame) -> dict:
        """Devuelve {'esperado', 'bajo', 'alto'}: matrices (n, 30) en soles para los dias 1 a 30."""
        lo, mid, hi = self._interpolar(df)
        seg = df["segmento"].to_numpy()
        for d in range(1, H):
            qs = np.array([self.q_seg[d].get(int(s), self.q_global[d]) for s in seg])
            lo[:, d], hi[:, d] = lo[:, d] - qs, hi[:, d] + qs
        esc, base = df["escala"].to_numpy()[:, None], df["saldo_t"].to_numpy()[:, None]
        esperado, bajo, alto = base + mid[:, 1:] * esc, base + lo[:, 1:] * esc, base + hi[:, 1:] * esc
        p30 = self.modelo30.predecir(df)   # el dia 30 es la salida del modelo validado, tal cual
        esperado[:, -1], bajo[:, -1], alto[:, -1] = p30["saldo_esperado"].to_numpy(), p30["saldo_bajo"].to_numpy(), p30["saldo_alto"].to_numpy()
        return {"esperado": esperado, "bajo": np.minimum(bajo, esperado), "alto": np.maximum(alto, esperado)}


def metricas_por_dia(df: pd.DataFrame, pred: dict) -> pd.DataFrame:
    """Para cada dia 1..30: cobertura de la banda, error relativo al ingreso y ancho relativo. df debe traer los objetivos y la escala."""
    filas = []
    esc, base = df["escala"].to_numpy(), df["saldo_t"].to_numpy()
    for d in range(1, H + 1):
        y = base + df[objetivo(d)].to_numpy() * esc
        e, lo, hi = pred["esperado"][:, d - 1], pred["bajo"][:, d - 1], pred["alto"][:, d - 1]
        filas.append({"dia": d, "cobertura_80": float(((y >= lo) & (y <= hi)).mean()), "mae_rel_ingreso": float((np.abs(e - y) / esc).mean()), "ancho_rel": float(((hi - lo) / esc).mean())})
    return pd.DataFrame(filas).set_index("dia")


def linea_base_lineal(df: pd.DataFrame, pred30: pd.DataFrame) -> dict:
    """Baseline ingenuo: ir en linea recta del saldo de hoy al saldo esperado del dia 30, con banda que crece con la raiz del tiempo hasta la del dia 30."""
    f = np.arange(1, H + 1)[None, :] / H
    base = df["saldo_t"].to_numpy()[:, None]
    e30, lo30, hi30 = (pred30[c].to_numpy()[:, None] for c in ("saldo_esperado", "saldo_bajo", "saldo_alto"))
    return {"esperado": base + (e30 - base) * f, "bajo": base + (lo30 - base) * np.sqrt(f), "alto": base + (hi30 - base) * np.sqrt(f)}


def linea_base_ma3(df: pd.DataFrame, cuant: tuple) -> dict:
    """Plan original: el neto medio de los ultimos 3 meses repartido en partes iguales por dia; banda con cuantiles de residuos de calibracion por dia (cuant: (lo[d], hi[d]) por dia)."""
    esc, base, mu = df["escala"].to_numpy()[:, None], df["saldo_t"].to_numpy()[:, None], df["net_ma3"].to_numpy()[:, None]
    d = np.arange(1, H + 1)[None, :]
    centro = mu * d / H
    return {"esperado": base + centro * esc, "bajo": base + (centro + np.array(cuant[0])[None, :]) * esc, "alto": base + (centro + np.array(cuant[1])[None, :]) * esc}


def cuantiles_residuo_ma3(cal: pd.DataFrame, alfa: float = 0.2) -> tuple:
    lo, hi = [], []
    for d in range(1, H + 1):
        r = cal[objetivo(d)].to_numpy() - cal["net_ma3"].to_numpy() * d / H
        lo.append(float(np.quantile(r, alfa / 2)))
        hi.append(float(np.quantile(r, 1 - alfa / 2)))
    return lo, hi
