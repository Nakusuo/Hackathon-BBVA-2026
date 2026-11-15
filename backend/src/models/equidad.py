"""Control de sesgo: error y cobertura por grupo (con y sin pesos muestrales) y comparacion de estrategias de remuestreo."""
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.isotonic import IsotonicRegression
import lightgbm as lgb

from src.models import pronostico as P


def por_grupo(df: pd.DataFrame, pred: pd.DataFrame, grupo: pd.Series, peso: pd.Series | None = None, minimo: int = 200) -> pd.DataFrame:
    """MAE relativo al ingreso, cobertura de la banda al 80 % y ancho de banda por grupo. Grupos con menos de `minimo` origenes se omiten."""
    err = (pred["saldo_esperado"] - df["y_saldo"]).abs() / df["escala"]
    dentro = ((df["y_saldo"] >= pred["saldo_bajo"]) & (df["y_saldo"] <= pred["saldo_alto"])).astype(float)
    ancho = (pred["saldo_alto"] - pred["saldo_bajo"]) / df["escala"]
    w = peso if peso is not None else pd.Series(1.0, index=df.index)
    filas = {}
    for g, idx in grupo.groupby(grupo).groups.items():
        if len(idx) < minimo:
            continue
        ww = w.loc[idx]
        filas[g] = {"n": len(idx), "mae_rel": float(np.average(err.loc[idx], weights=ww)), "cobertura_80": float(np.average(dentro.loc[idx], weights=ww)),
                    "ancho_rel": float(np.average(ancho.loc[idx], weights=ww))}
    return pd.DataFrame(filas).T


def brechas(tabla: pd.DataFrame, umbral_cobertura: float = 0.05, razon_mae: float = 1.3) -> dict:
    """Diferencia entre el mejor y el peor grupo. Marca alerta si la cobertura difiere mas de 5 puntos o el error de un grupo supera 1,3 veces el del mejor."""
    cob = tabla["cobertura_80"]
    mae = tabla["mae_rel"]
    return {"brecha_cobertura": float(cob.max() - cob.min()), "razon_mae": float(mae.max() / mae.min()), "peor_grupo_mae": str(mae.idxmax()), "peor_grupo_cobertura": str(cob.idxmin()),
            "alerta": bool((cob.max() - cob.min()) > umbral_cobertura or (mae.max() / mae.min()) > razon_mae)}


def comparar_remuestreo(ent: pd.DataFrame, cal: pd.DataFrame, te: pd.DataFrame, features: list, semilla: int = 0) -> pd.DataFrame:
    """Riesgo de rojo (clase rara): sin ajuste, pesos de clase, submuestreo y SMOTE solo sobre el entrenamiento. Todas se calibran con la misma ventana."""
    X, y = ent[features].astype(float), ent["rojo30"].to_numpy()
    mediana = X.median()
    base = dict(P.PARAMS_BASE, n_estimators=250)
    estrategias = {}
    estrategias["sin ajuste"] = (X, y, None)
    estrategias["pesos de clase"] = (X, y, {"scale_pos_weight": float((1 - y.mean()) / y.mean())})
    Xu, yu = RandomUnderSampler(sampling_strategy=0.5, random_state=semilla).fit_resample(X.fillna(mediana), y)
    estrategias["submuestreo 1:2"] = (Xu, yu, None)
    Xs, ys = SMOTE(sampling_strategy=0.5, random_state=semilla, k_neighbors=5).fit_resample(X.fillna(mediana), y)
    estrategias["SMOTE 1:2"] = (Xs, ys, None)
    ant = (te["saldo_t"] > 0).to_numpy()
    filas = {}
    for nombre, (Xa, ya, extra) in estrategias.items():
        clf = lgb.LGBMClassifier(**{**base, **(extra or {})}).fit(Xa, ya)
        iso = IsotonicRegression(out_of_bounds="clip").fit(clf.predict_proba(cal[features].astype(float).fillna(mediana))[:, 1], cal["rojo30"])
        p = iso.predict(clf.predict_proba(te[features].astype(float).fillna(mediana))[:, 1])
        filas[nombre] = P.metricas_rojo(te["rojo30"].to_numpy()[ant], p[ant])
    return pd.DataFrame(filas).T
