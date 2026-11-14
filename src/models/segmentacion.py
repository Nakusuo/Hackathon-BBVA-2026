"""Segmentacion de clientes con K-Prototypes (variables mixtas) frente a reglas por umbral y K-Means.
Solo usa variables observables: lo que se ve en los movimientos y lo que el cliente declara."""
import os
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn
from kmodes.kprototypes import KPrototypes
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.comun.rutas import MODELOS
from src.models import datos
from src.models.columnas import OBSERVABLES_CLIENTE

NUMERICAS = ["ingreso_medio", "cv_ingreso", "fijo_sobre_ingreso", "cuota_sobre_ingreso", "gasto_sobre_ingreso", "pct_hormiga", "ahorro_pct",
             "dias_rojo_3m", "n_suscripciones", "pct_billetera", "volatilidad_gasto", "colchon_observado"]
CATEGORICAS = ["tipo_trabajo", "frecuencia_ingreso", "region"]
SUSCRIPCIONES = {"StreamFlix", "MusicaPlus", "JuegaMas", "VideoMax", "NubeDoc"}


def features_cliente(carpeta: str, hasta: str, meses: int = 12) -> pd.DataFrame:
    """Variables por cliente con datos anteriores a `hasta` (sin fuga hacia el futuro)."""
    cl = datos.cargar_clientes(carpeta)
    panel = datos.cargar_panel(carpeta)
    fin = pd.Period(pd.Timestamp(hasta) - pd.Timedelta(days=1), "M")
    ventana = [str(fin - i) for i in range(meses)]
    p = panel[panel["mes"].isin(ventana)].copy()
    g = p.groupby("customer_id")
    ingreso = g["ingreso_operativo"].mean()
    gasto_total = g[["gasto_fijo", "gasto_variable", "gasto_hormiga", "gasto_deuda"]].sum().sum(axis=1) / meses
    ultimos3 = p[p["mes"].isin(ventana[:3])].groupby("customer_id")["dias_en_rojo"].sum()
    gastos_mes = p.assign(gt=p[["gasto_fijo", "gasto_variable", "gasto_hormiga", "gasto_deuda"]].sum(axis=1)).groupby("customer_id")["gt"]
    sin_grati = p[~p["mes"].str[-2:].isin(["07", "12"])].groupby("customer_id")["ingreso_operativo"]
    tx = datos.cargar_transacciones(carpeta, ["customer_id", "comercio", "canal", "fecha_hora"], desde=pd.Timestamp(hasta) - pd.DateOffset(months=3), hasta=hasta)
    tx["comercio"] = tx["comercio"].astype(str)
    tx["canal"] = tx["canal"].astype(str)
    subs = tx[tx["comercio"].isin(SUSCRIPCIONES)].groupby("customer_id")["comercio"].nunique()
    billetera = tx.assign(b=tx["canal"].isin(["billetera", "pago_qr"])).groupby("customer_id")["b"].mean()
    f = pd.DataFrame(index=ingreso.index)
    f["ingreso_medio"] = ingreso
    f["cv_ingreso"] = sin_grati.std() / sin_grati.mean()
    f["fijo_sobre_ingreso"] = (g["gasto_fijo"].sum() + g["gasto_deuda"].sum()) / meses / ingreso
    f["cuota_sobre_ingreso"] = cl["cuota_mensual"].reindex(f.index) / ingreso
    f["gasto_sobre_ingreso"] = gasto_total / ingreso
    f["pct_hormiga"] = g["gasto_hormiga"].sum() / meses / gasto_total
    f["ahorro_pct"] = g["ahorro_movido"].sum() / meses / ingreso
    f["dias_rojo_3m"] = ultimos3.reindex(f.index).fillna(0)
    f["n_suscripciones"] = subs.reindex(f.index).fillna(0)
    f["pct_billetera"] = billetera.reindex(f.index).fillna(0)
    f["volatilidad_gasto"] = gastos_mes.std() / gastos_mes.mean()
    f["colchon_observado"] = g["saldo_fin"].mean() / ingreso
    for c in CATEGORICAS:
        f[c] = cl[c].reindex(f.index).astype(str)
    return f.replace([np.inf, -np.inf], np.nan).fillna(f.median(numeric_only=True))


class Preparador:
    """Transformacion fijada con los datos de entrenamiento: log a las variables con cola, winsor y estandarizacion."""

    LOG = ["ingreso_medio", "cuota_sobre_ingreso", "dias_rojo_3m", "n_suscripciones"]

    def ajustar(self, f: pd.DataFrame) -> "Preparador":
        x = self._pre(f, None)
        self.lim = (x.quantile(0.01), x.quantile(0.99))
        self.scaler = StandardScaler().fit(x.clip(self.lim[0], self.lim[1], axis=1))
        return self

    def _pre(self, f, lim):
        x = f[NUMERICAS].astype(float).copy()
        for c in self.LOG:
            x[c] = np.log1p(x[c].clip(lower=0))
        return x

    def numericas(self, f: pd.DataFrame) -> np.ndarray:
        x = self._pre(f, None).clip(self.lim[0], self.lim[1], axis=1)
        return self.scaler.transform(x)

    def matriz(self, f: pd.DataFrame) -> np.ndarray:
        return np.hstack([self.numericas(f), f[CATEGORICAS].to_numpy(dtype=object)])


def distancia_gower(num: np.ndarray, cat: np.ndarray) -> np.ndarray:
    rango = np.ptp(num, axis=0)
    rango[rango == 0] = 1
    dn = np.abs(num[:, None, :] - num[None, :, :]) / rango
    dc = (cat[:, None, :] != cat[None, :, :]).astype(float)
    return (dn.sum(2) + dc.sum(2)) / (num.shape[1] + cat.shape[1])


def ajustar_kprototypes(X: np.ndarray, k: int, semilla: int = 0, n_init: int = 4) -> KPrototypes:
    ncat = len(CATEGORICAS)
    kp = KPrototypes(n_clusters=k, init="Cao", n_init=n_init, random_state=semilla, n_jobs=1)
    kp.fit(X, categorical=list(range(X.shape[1] - ncat, X.shape[1])))
    return kp


def predecir_kp(kp: KPrototypes, X: np.ndarray) -> np.ndarray:
    ncat = len(CATEGORICAS)
    return kp.predict(X, categorical=list(range(X.shape[1] - ncat, X.shape[1])))


def estabilidad(X: np.ndarray, k: int, n_pares: int = 8, semilla: int = 0) -> float:
    """ARI medio entre pares de modelos ajustados en submuestras distintas, comparados sobre todos los clientes."""
    rng = np.random.default_rng(semilla)
    n = len(X)
    etiquetas = []
    for i in range(n_pares * 2):
        idx = rng.choice(n, int(0.8 * n), replace=False)
        etiquetas.append(predecir_kp(ajustar_kprototypes(X[idx], k, semilla=i, n_init=2), X))
    return float(np.mean([adjusted_rand_score(etiquetas[2 * j], etiquetas[2 * j + 1]) for j in range(n_pares)]))


def evaluar_k(f: pd.DataFrame, prep: Preparador, ks=range(3, 9), semilla: int = 0) -> pd.DataFrame:
    X = prep.matriz(f)
    num = prep.numericas(f)
    cat = f[CATEGORICAS].to_numpy(dtype=object)
    D = distancia_gower(num, cat)
    filas = []
    for k in ks:
        kp = ajustar_kprototypes(X, k, semilla)
        lab = predecir_kp(kp, X)
        filas.append({"k": k, "costo": kp.cost_, "silueta_gower": silhouette_score(D, lab, metric="precomputed"),
                      "estabilidad_ari": estabilidad(X, k, semilla=semilla), "tamano_min": int(np.bincount(lab).min())})
    r = pd.DataFrame(filas).set_index("k")
    r["puntaje"] = 0.5 * (r["silueta_gower"] - r["silueta_gower"].min()) / (np.ptp(r["silueta_gower"]) or 1) + 0.5 * r["estabilidad_ari"]
    return r


def baseline_reglas(f: pd.DataFrame) -> np.ndarray:
    """Matriz ahorro x gasto por umbrales fijos (la alternativa sencilla)."""
    ahorra = f["ahorro_pct"] >= 0.05
    gasta_mucho = f["gasto_sobre_ingreso"] >= f["gasto_sobre_ingreso"].median()
    return (ahorra.astype(int) * 2 + gasta_mucho.astype(int)).to_numpy()


def baseline_kmeans(prep: Preparador, f: pd.DataFrame, k: int, semilla: int = 0) -> np.ndarray:
    cat = pd.get_dummies(f[CATEGORICAS]).to_numpy(dtype=float)
    X = np.hstack([prep.numericas(f), cat * 0.5])
    return KMeans(n_clusters=k, n_init=10, random_state=semilla).fit_predict(X)


def comparar_con_etiquetas(etiquetas: dict, cl: pd.DataFrame, idx) -> pd.DataFrame:
    ref = {"arquetipo": cl.loc[idx, "arquetipo"], "segmento_real": cl.loc[idx, "segmento"],
           "perfil_2x2": cl.loc[idx, "perfil_ahorro_real"] + "|" + cl.loc[idx, "perfil_gasto_real"]}
    return pd.DataFrame({m: {r: adjusted_rand_score(v, lab) for r, v in ref.items()} for m, lab in etiquetas.items()}).T


def describir(f: pd.DataFrame, etiquetas: np.ndarray) -> pd.DataFrame:
    """Nombre y descripcion en palabras de cada segmento a partir de sus medianas frente a la poblacion."""
    g = f.assign(seg=etiquetas)
    med = g.groupby("seg")[NUMERICAS].median()
    glob = f[NUMERICAS].median()
    filas = []
    for s, r in med.iterrows():
        rasgos = []
        if r["cv_ingreso"] > 1.3 * glob["cv_ingreso"]:
            rasgos.append("ingreso irregular")
        elif r["cv_ingreso"] < 0.8 * glob["cv_ingreso"]:
            rasgos.append("ingreso estable")
        if r["dias_rojo_3m"] > max(glob["dias_rojo_3m"], 0.5) * 2:
            rasgos.append("tension de caja")
        if r["ahorro_pct"] > 1.5 * max(glob["ahorro_pct"], 0.01):
            rasgos.append("ahorra")
        elif r["gasto_sobre_ingreso"] > 1.08 * glob["gasto_sobre_ingreso"]:
            rasgos.append("gasta casi todo")
        if r["pct_hormiga"] > 1.3 * glob["pct_hormiga"]:
            rasgos.append("gasto hormiga alto")
        if r["ingreso_medio"] > 1.25 * glob["ingreso_medio"]:
            rasgos.append("ingreso alto")
        elif r["ingreso_medio"] < 0.8 * glob["ingreso_medio"]:
            rasgos.append("ingreso bajo")
        tipo = g[g["seg"] == s]["tipo_trabajo"].mode().iat[0]
        filas.append({"segmento": s, "n": int((g["seg"] == s).sum()), "tipo_trabajo_frecuente": tipo, "nombre": " · ".join(rasgos[:3]) or "perfil medio",
                      **{c: round(float(r[c]), 3) for c in NUMERICAS}})
    return pd.DataFrame(filas).set_index("segmento")


def entrenar_arranque_en_frio(f: pd.DataFrame, etiquetas: np.ndarray, semilla: int = 0):
    """Predice el segmento solo con lo que el cliente declara (las 5 preguntas), para quien aun no tiene historial."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    X = pd.get_dummies(f[CATEGORICAS], dtype=float)
    X["cuota_sobre_ingreso"] = f["cuota_sobre_ingreso"].to_numpy()
    modelo = RandomForestClassifier(n_estimators=200, min_samples_leaf=3, random_state=semilla, n_jobs=1)
    cv = cross_val_score(modelo, X, etiquetas, cv=5)
    modelo.fit(X, etiquetas)
    return modelo, list(X.columns), float(cv.mean())


def guardar(modelo: dict, nombre: str = "segmentacion") -> str:
    os.makedirs(MODELOS, exist_ok=True)
    modelo["manifiesto"] = {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__,
                            "observables": OBSERVABLES_CLIENTE, "numericas": NUMERICAS, "categoricas": CATEGORICAS}
    ruta = os.path.join(MODELOS, f"{nombre}.pkl")
    joblib.dump(modelo, ruta, compress=3)
    return ruta


def asignar(modelo: dict, f: pd.DataFrame) -> np.ndarray:
    return predecir_kp(modelo["kp"], modelo["prep"].matriz(f))


def elegir_k(tabla: pd.DataFrame, umbral_estabilidad: float = 0.60) -> int:
    """Mayor silueta entre los k cuya estabilidad llega al umbral; si ninguno llega, el de mayor estabilidad."""
    ok = tabla[tabla["estabilidad_ari"] >= umbral_estabilidad]
    return int(ok["silueta_gower"].idxmax()) if len(ok) else int(tabla["estabilidad_ari"].idxmax())


def entrenar(carpeta: str, hasta: str, ks=range(3, 9), semilla: int = 0) -> dict:
    f = features_cliente(carpeta, hasta)
    prep = Preparador().ajustar(f)
    tabla = evaluar_k(f, prep, ks, semilla)
    k = elegir_k(tabla)
    X = prep.matriz(f)
    kp = ajustar_kprototypes(X, k, semilla, n_init=8)
    lab = predecir_kp(kp, X)
    frio, cols, acc = entrenar_arranque_en_frio(f, lab, semilla)
    return {"kp": kp, "prep": prep, "k": k, "tabla_k": tabla, "descripcion": describir(f, lab), "frio": frio, "frio_cols": cols, "frio_acc": acc,
            "hasta": hasta, "semilla": semilla, "features": f, "etiquetas": lab}
