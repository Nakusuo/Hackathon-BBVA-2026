"""Modelos sobre movimientos y texto: categoria de la glosa, recurrentes y suscripciones duplicadas, atipicos y sentimiento.
Cada uno se compara con su alternativa sencilla."""
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import SGDClassifier

SUBS = {"StreamFlix", "MusicaPlus", "JuegaMas", "VideoMax", "NubeDoc"}


def normalizar(s) -> str:
    if not isinstance(s, str):
        return ""
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()


# ---------------------------------------------------------------- glosa -> categoria
def entrenar_glosa(tx: pd.DataFrame, corte: str = "2024-01-01", max_filas: int = 120_000, semilla: int = 0) -> dict:
    d = tx.dropna(subset=["glosa", "categoria"])
    ent = d[d["fecha_hora"] < corte]
    pru = d[d["fecha_hora"] >= corte]
    ent = ent.sample(min(len(ent), max_filas), random_state=semilla)
    pru = pru.sample(min(len(pru), 30_000), random_state=semilla)
    ent = ent.assign(glosa_n=ent["glosa"].map(normalizar))
    pru = pru.assign(glosa_n=pru["glosa"].map(normalizar))
    # alternativa sencilla: diccionario exacto glosa normalizada -> categoria mas frecuente; lo no visto va a "otros"
    cnt = ent.assign(categoria=ent["categoria"].astype(str)).groupby(["glosa_n", "categoria"]).size().rename("n").reset_index()
    dic = dict(cnt.sort_values("n", ascending=False).drop_duplicates("glosa_n")[["glosa_n", "categoria"]].itertuples(index=False, name=None))
    base = pru["glosa_n"].map(dic).fillna("otros")
    modelo = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=3, max_features=150_000, sublinear_tf=True), SGDClassifier(loss="modified_huber", alpha=2e-6, max_iter=25, tol=1e-4, n_jobs=8, random_state=semilla))
    modelo.fit(ent["glosa_n"], ent["categoria"].astype(str))
    pred = modelo.predict(pru["glosa_n"])
    y = pru["categoria"].astype(str)
    cubre = pru["glosa_n"].isin(dic).mean()
    return {"modelo": modelo, "diccionario": dic, "resultados": {
        "diccionario": {"f1_macro": f1_score(y, base.astype(str), average="macro"), "exactitud": accuracy_score(y, base.astype(str))},
        "tfidf_char_sgd_lineal": {"f1_macro": f1_score(y, pred, average="macro"), "exactitud": accuracy_score(y, pred)}, "cobertura_diccionario": float(cubre),
        "n_prueba": len(pru)}, "pred": pred, "real": y.to_numpy()}


# ---------------------------------------------------------------- recurrentes y duplicadas
def _brechas(tx: pd.DataFrame) -> pd.DataFrame:
    d = tx.dropna(subset=["monto"]).sort_values(["customer_id", "comercio", "fecha_hora"])
    d["gap"] = d.groupby(["customer_id", "comercio"], observed=True)["fecha_hora"].diff().dt.total_seconds() / 86400
    return d


def detectar_recurrentes(tx: pd.DataFrame, tol_cv_monto: float = 0.20, tol_mad_dias: float = 4.0) -> pd.Series:
    """Comercio con >=3 cobros, intervalo mensual o quincenal estable y monto casi constante. Devuelve bool por fila del indice de tx."""
    d = _brechas(tx)
    g = d.groupby(["customer_id", "comercio"], observed=True)
    est = g.agg(n=("gap", "size"), mediana=("gap", "median"), mad=("gap", lambda s: (s - s.median()).abs().median()), cv=("monto", lambda s: s.std() / s.mean() if s.mean() else np.inf))
    mensual = est["mediana"].between(26, 34)
    quincenal = est["mediana"].between(13, 17)
    ok = (est["n"] >= 3) & (mensual | quincenal) & (est["mad"] <= tol_mad_dias) & (est["cv"] <= tol_cv_monto)
    claves = pd.MultiIndex.from_frame(d[["customer_id", "comercio"]])
    flag = pd.Series(ok.reindex(claves).fillna(False).to_numpy(), index=d.index)
    return flag.reindex(tx.index, fill_value=False)


def baseline_mismo_comercio(tx: pd.DataFrame, minimo: int = 3) -> pd.Series:
    n = tx.groupby(["customer_id", "comercio"], observed=True)["comercio"].transform("size")
    return n >= minimo


def detectar_suscripciones_duplicadas(tx: pd.DataFrame) -> set:
    """Clientes con dos cobros del mismo servicio de suscripcion en la mayoria de los meses."""
    d = tx[tx["comercio"].astype(str).isin(SUBS)].copy()
    d["mes"] = d["fecha_hora"].dt.to_period("M")
    por_mes = d.groupby(["customer_id", "comercio", "mes"], observed=True).size().rename("n").reset_index()
    frac = por_mes.groupby(["customer_id", "comercio"], observed=True)["n"].agg(lambda s: (s >= 2).mean())
    return set(frac[frac >= 0.5].index.get_level_values(0).astype(str))


def prf(y, pred) -> dict:
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {"precision": float(p), "recall": float(r), "f1": float(f)}


# ---------------------------------------------------------------- atipicos
def _features_atipicos(tx: pd.DataFrame) -> pd.DataFrame:
    d = tx.dropna(subset=["monto_pen"]).copy()
    d["lm"] = np.log1p(d["monto_pen"].astype(float))
    g = d.groupby(["customer_id", "categoria"], observed=True)["lm"]
    d["med"] = g.transform("median")
    d["dev"] = (d["lm"] - d["med"]).abs()
    d["mad"] = d.groupby(["customer_id", "categoria"], observed=True)["dev"].transform("median") + 0.05
    d["z"] = (d["lm"] - d["med"]) / (1.4826 * d["mad"])
    d["hora"] = d["fecha_hora"].dt.hour
    d["comercio_nuevo"] = (d.groupby(["customer_id", "comercio"], observed=True).cumcount() == 0).astype(int)
    d["tc"] = (d["canal"].astype(str) == "tarjeta_credito").astype(int)
    d["madrugada"] = d["hora"].between(1, 5).astype(int)
    return d


def evaluar_atipicos(tx: pd.DataFrame, semilla: int = 0, max_filas: int = 800_000) -> dict:
    d = _features_atipicos(tx[tx["tipo"] == "gasto"])
    d = d.sample(min(len(d), max_filas), random_state=semilla)
    y = d["es_atipico"].to_numpy().astype(int)
    k = int(y.sum())
    z = d["z"].to_numpy()
    iso = IsolationForest(n_estimators=150, contamination="auto", random_state=semilla, n_jobs=4)
    X = d[["z", "hora", "comercio_nuevo", "tc", "madrugada", "lm"]].to_numpy()
    iso.fit(X)
    puntaje = -iso.score_samples(X)

    def al_k(score):
        top = np.argsort(-score)[:k]
        return {"precision_en_k": float(y[top].mean()), "recall_en_k": float(y[top].sum() / max(k, 1))}
    return {"n_atipicos": k, "n": len(d), "zscore_robusto": al_k(z), "isolation_forest": al_k(puntaje)}


# ---------------------------------------------------------------- sentimiento
FRASES_A_MANO = [  # escritas a mano, fuera de las plantillas del generador, para no medir solo contra lo que el modelo vio
    ("Hoy me pagaron y por fin respiro", "positivo"), ("Logre juntar para el colegio de mi hijo sin pedir prestado", "positivo"),
    ("Mis cuentas estan al dia, que alivio", "positivo"), ("Me sobro plata este mes, la guardo", "positivo"), ("Ya termine de pagar la deuda del celular", "positivo"),
    ("Esta semana vendi bien y estoy tranquilo", "positivo"),
    ("Cuanto me queda para la semana", "neutro"), ("Quiero ver el detalle de mis pagos de luz y agua", "neutro"), ("Que dia vence mi tarjeta", "neutro"),
    ("Necesito saber cuanto gaste en transporte", "neutro"), ("Como cambio mi meta de ahorro", "neutro"), ("Muestrame mis ingresos de los ultimos tres meses", "neutro"),
    ("No se si alcanzare a pagar el alquiler", "preocupado"), ("Estoy raspando la olla este mes y me inquieta", "preocupado"),
    ("Me preocupa que no entren clientes esta quincena", "preocupado"), ("Creo que me voy a quedar corto con los gastos del colegio", "preocupado"),
    ("Siento que el sueldo ya no me rinde como antes", "preocupado"), ("Se me juntaron las cuotas y estoy apurado", "preocupado"),
    ("Estoy sin un sol y todavia faltan diez dias", "negativo"), ("Ya no aguanto mas con tantas deudas", "negativo"), ("No tengo con que comprar comida hoy", "negativo"),
    ("Me cortaron el servicio por no pagar y estoy desesperado", "negativo"), ("Perdi el trabajo y no se que hacer", "negativo"), ("Otra vez en numeros rojos, estoy harto", "negativo"),
]
LEXICO = {"positivo": {"alivio", "tranquilo", "sobro", "pagaron", "guardo", "termine", "logre", "respiro", "bien", "ahorre", "dia"},
          "preocupado": {"preocupa", "inquieta", "apurado", "corto", "alcanzare", "alcanza", "miedo", "justo", "rinde", "juntaron"},
          "negativo": {"harto", "desesperado", "rojo", "rojos", "deudas", "perdi", "cortaron", "aguanto", "sin", "ahogado", "salida"}}


def baseline_lexico(textos) -> np.ndarray:
    out = []
    for t in textos:
        pal = set(normalizar(t).split())
        punt = {k: len(pal & v) for k, v in LEXICO.items()}
        mejor = max(punt, key=punt.get)
        out.append(mejor if punt[mejor] > 0 else "neutro")
    return np.array(out)


def entrenar_sentimiento(ms: pd.DataFrame, corte: str = "2024-01-01", semilla: int = 0) -> dict:
    ent, pru = ms[ms["fecha_hora"] < corte], ms[ms["fecha_hora"] >= corte]
    modelo = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, preprocessor=normalizar), LogisticRegression(C=4, max_iter=400, random_state=semilla))
    modelo.fit(ent["texto"], ent["sentimiento"].astype(str))
    x_m, y_m = [f for f, _ in FRASES_A_MANO], np.array([e for _, e in FRASES_A_MANO])
    res = {}
    for nombre, X, y in (("plantillas_futuras", pru["texto"], pru["sentimiento"].astype(str).to_numpy()), ("escritas_a_mano", x_m, y_m)):
        res[nombre] = {"lexico_f1": f1_score(y, baseline_lexico(X), average="macro"), "tfidf_lr_f1": f1_score(y, modelo.predict(X), average="macro"), "n": len(y)}
    return {"modelo": modelo, "resultados": res}


def columnas_texto(origenes: pd.DataFrame, ids: np.ndarray, fechas: pd.DatetimeIndex, ms: pd.DataFrame, modelo, ventana: int = 30) -> pd.DataFrame:
    """Mensajes de los ultimos `ventana` dias por origen, con el sentimiento PREDICHO (nunca la etiqueta)."""
    ms = ms.copy()
    ms["customer_id"] = ms["customer_id"].astype(str)
    ms["pred"] = modelo.predict(ms["texto"])
    pos_c = pd.Series(np.arange(len(ids)), index=ids)
    ms["c"] = ms["customer_id"].map(pos_c)
    ms["d"] = fechas.searchsorted(ms["fecha_hora"].dt.normalize())
    B, D = len(ids), len(fechas)
    estres, total = np.zeros((B, D), np.float32), np.zeros((B, D), np.float32)
    np.add.at(total, (ms["c"].to_numpy(), ms["d"].to_numpy()), 1)
    m = ms["pred"].isin(["preocupado", "negativo"]).to_numpy()
    np.add.at(estres, (ms["c"].to_numpy()[m], ms["d"].to_numpy()[m]), 1)
    cs_e = np.concatenate([np.zeros((B, 1), np.float32), np.cumsum(estres, 1)], 1)
    cs_t = np.concatenate([np.zeros((B, 1), np.float32), np.cumsum(total, 1)], 1)
    c, t = origenes["cliente_idx"].to_numpy(), origenes["dia_idx"].to_numpy()
    e = cs_e[c, t + 1] - cs_e[c, np.maximum(t + 1 - ventana, 0)]
    n = cs_t[c, t + 1] - cs_t[c, np.maximum(t + 1 - ventana, 0)]
    return pd.DataFrame({"msg_n_30": n, "msg_estres_30": e, "msg_frac_estres_30": np.where(n > 0, e / np.maximum(n, 1), np.nan)}, index=origenes.index)
