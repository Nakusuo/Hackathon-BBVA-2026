"""Pronostico de liquidez a 30 dias: saldo esperado, banda al 80 %, probabilidad de quedar en rojo y dia de riesgo.
Modelos: promedio movil (baseline del plan), perfil estructural por calendario y LightGBM cuantilico con conformal por segmento."""
import os
import platform

import warnings

import holidays
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from src.comun.rutas import MODELOS
from src.models.datos import Series

warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")
H = 30
MIN_HIST = 91
EVENT_COLS_PREFIX = "fuerza_"
CAT_DECL = ["tipo_trabajo", "frecuencia_ingreso", "region", "rango_edad"]
PARAMS_BASE = dict(n_estimators=500, learning_rate=0.05, num_leaves=31, min_child_samples=40, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                   reg_lambda=1.0, verbose=-1, n_jobs=8)


def _ventana(cs: np.ndarray, t: np.ndarray, w: int) -> np.ndarray:
    return cs[:, t + 1] - cs[:, t + 1 - w]


def _indices_mes_anterior(fechas: pd.DatetimeIndex, k: int) -> np.ndarray:
    previas = fechas - pd.DateOffset(months=k)
    idx = fechas.searchsorted(previas)
    ok = (idx < len(fechas)) & (fechas[np.minimum(idx, len(fechas) - 1)] == previas)
    return np.where(ok, idx, -1)


def construir_origenes(s: Series, clientes: pd.DataFrame, contexto: pd.DataFrame, segmento: dict | None = None, paso: int = 7, tramo: int = 100,
                       origenes_dias=None) -> pd.DataFrame:
    """Una fila por (cliente, origen) con variables observables hasta el origen y los objetivos a 30 dias."""
    B, D = s.ing.shape
    fechas = s.fechas
    origenes = np.asarray(origenes_dias, dtype=int) if origenes_dias is not None else np.arange(MIN_HIST - 1, D - H - 1, paso)
    n_o = len(origenes)
    cs_i = np.concatenate([np.zeros((B, 1), np.float64), np.cumsum(s.ing, axis=1)], axis=1)
    cs_g = np.concatenate([np.zeros((B, 1), np.float64), np.cumsum(s.gas, axis=1)], axis=1)
    cs_r = np.concatenate([np.zeros((B, 1), np.float64), np.cumsum(s.saldo < 0, axis=1)], axis=1)
    prev = np.stack([_indices_mes_anterior(fechas, k) for k in (1, 2, 3)])
    ev = contexto[[c for c in contexto.columns if c.startswith(EVENT_COLS_PREFIX)]].to_numpy(np.float32)
    ev_max = ev.max(axis=1) if ev.size else np.zeros(D, np.float32)
    feri = holidays.country_holidays("PE", years=range(fechas[0].year, fechas[-1].year + 2))
    es_feriado = np.array([f.date() in feri for f in fechas], dtype=np.float32)
    fm, fd = np.asarray(fechas.month), np.asarray(fechas.day)
    grati = (np.isin(fm, [7, 12]) & (fd == 15)).astype(np.float32)
    navidad = ((fm == 12) & (fd >= 10)).astype(np.float32)
    escolar = (fm == 3).astype(np.float32)
    dia15 = (fd == 15).astype(np.float32)
    finmes = np.asarray(fechas.is_month_end).astype(np.float32)

    def en_h(arr, t):  # suma del arreglo sobre los dias t+1..t+H
        c = np.concatenate([[0], np.cumsum(arr)])
        return c[t + 1 + H] - c[t + 1]

    def dias_hasta(arr, t):
        c = np.flatnonzero(arr > 0)
        pos = np.searchsorted(c, t + 1)
        return np.where(pos < len(c), c[np.minimum(pos, len(c) - 1)] - t, 60)

    filas = []
    for a in range(0, B, tramo):
        sl = slice(a, min(a + tramo, B))
        b = sl.stop - sl.start
        t = origenes
        ing30, gas30 = _ventana(cs_i[sl], t, 30), _ventana(cs_g[sl], t, 30)
        ing60, gas60 = _ventana(cs_i[sl], t, 60) / 2, _ventana(cs_g[sl], t, 60) / 2
        ing90, gas90 = _ventana(cs_i[sl], t, 90) / 3, _ventana(cs_g[sl], t, 90) / 3
        escala = np.maximum(ing90, 100.0)
        semanas = np.stack([cs_i[sl][:, t + 1 - 7 * k] - cs_i[sl][:, t + 1 - 7 * (k + 1)] for k in range(13)], axis=-1)
        cv = semanas.std(-1) / np.maximum(semanas.mean(-1), 1.0)
        saldo_t = s.saldo[sl][:, t]
        ly = np.where(t >= 365 + 30, cs_i[sl][:, np.maximum(t + 1 - 335, 0)] - cs_i[sl][:, np.maximum(t + 1 - 365, 0)], np.nan)
        ly_g = np.where(t >= 365 + 30, cs_g[sl][:, np.maximum(t + 1 - 335, 0)] - cs_g[sl][:, np.maximum(t + 1 - 365, 0)], np.nan)
        # perfil estructural: lo ocurrido el mismo dia del mes en los 3 meses anteriores (solo dias ya observados)
        j = np.arange(1, H + 1)
        sdia = t[:, None] + j[None, :]
        exp_i = np.zeros((b, n_o, H), np.float32)
        exp_g = np.zeros((b, n_o, H), np.float32)
        cnt = np.zeros((n_o, H), np.float32)
        for k in range(3):
            p = prev[k][sdia]
            ok = (p >= 0) & (p <= t[:, None])
            pc = np.where(ok, p, 0)
            exp_i += np.where(ok[None], s.ing[sl][:, pc], 0)
            exp_g += np.where(ok[None], s.gas[sl][:, pc], 0)
            cnt += ok
        cnt = np.maximum(cnt, 1)
        exp_i /= cnt[None]
        exp_g /= cnt[None]
        trayecto = saldo_t[:, :, None] + np.cumsum(exp_i - exp_g, axis=2)
        st_net = (exp_i - exp_g).sum(2)
        st_min_rel = trayecto.min(2) / escala
        st_dia = np.where((trayecto < 0).any(2), (trayecto < 0).argmax(2) + 1, H + 1)
        # objetivos
        fut = np.stack([s.saldo[sl][:, t + jj] for jj in j], axis=-1)
        y_saldo = fut[:, :, -1]
        y_min = fut.min(2)
        y_dia = np.where((fut < 0).any(2), (fut < 0).argmax(2) + 1, 0)
        cols = {
            "cliente_idx": np.repeat(np.arange(sl.start, sl.stop), n_o), "dia_idx": np.tile(t, b), "saldo_t": saldo_t.ravel(), "escala": escala.ravel(),
            "saldo_rel": (saldo_t / escala).ravel(), "ing30": (ing30 / escala).ravel(), "ing60": (ing60 / escala).ravel(), "ing90": (ing90 / escala).ravel(),
            "gas30": (gas30 / escala).ravel(), "gas60": (gas60 / escala).ravel(), "gas90": (gas90 / escala).ravel(), "cv_semanal": cv.ravel(),
            "dias_rojo_90": _ventana(cs_r[sl], t, 90).ravel(), "ing_ano_prev": (ly / escala).ravel(), "gas_ano_prev": (ly_g / escala).ravel(),
            "net_ma3": ((ing90 - gas90) / escala).ravel(), "st_net": (st_net / escala).ravel(), "st_min_rel": st_min_rel.ravel(), "st_dia": st_dia.ravel(),
            "st_ing": (exp_i.sum(2) / escala).ravel(), "st_gas": (exp_g.sum(2) / escala).ravel(),
            "dias_a_15": np.tile(dias_hasta(dia15, t), b), "dias_a_fin": np.tile(dias_hasta(finmes, t), b), "grati_h": np.tile(en_h(grati, t), b),
            "navidad_h": np.tile(en_h(navidad, t), b), "escolar_h": np.tile(en_h(escolar, t), b), "feriados_h": np.tile(en_h(es_feriado, t), b),
            "mes_sin": np.tile(np.sin(2 * np.pi * fm[t] / 12), b), "mes_cos": np.tile(np.cos(2 * np.pi * fm[t] / 12), b),
            "ev_ahora": np.tile(ev_max[t], b), "ev_horizonte": np.tile(np.array([ev_max[x + 1:x + 1 + H].mean() for x in t]), b),
            "y_saldo": y_saldo.ravel(), "y_net_n": ((y_saldo - saldo_t) / escala).ravel(), "y_min": y_min.ravel(), "y_dia": y_dia.ravel(),
        }
        filas.append(pd.DataFrame(cols))
    df = pd.concat(filas, ignore_index=True)
    df["fecha"] = fechas[df["dia_idx"].to_numpy()]
    cl = clientes.reindex(s.ids)
    for c in CAT_DECL:
        df[c] = cl[c].astype("category").cat.codes.to_numpy()[df["cliente_idx"].to_numpy()]
    df["personas_a_cargo"] = cl["personas_a_cargo"].to_numpy()[df["cliente_idx"].to_numpy()]
    df["colchon_meses"] = cl["colchon_meses"].to_numpy()[df["cliente_idx"].to_numpy()]
    df["paga_en_usd"] = cl["paga_en_usd"].astype(int).to_numpy()[df["cliente_idx"].to_numpy()]
    df["cuota_rel"] = cl["cuota_mensual"].to_numpy()[df["cliente_idx"].to_numpy()] / df["escala"]
    df["segmento"] = (np.array([segmento[i] for i in s.ids])[df["cliente_idx"].to_numpy()] if segmento else -1)
    df["rojo30"] = (df["y_min"] < 0).astype(int)
    return df.astype({c: "float32" for c in df.columns if df[c].dtype == "float64"})


FEATURES_BASE = ["saldo_rel", "ing30", "ing60", "ing90", "gas30", "gas60", "gas90", "cv_semanal", "dias_rojo_90", "ing_ano_prev", "gas_ano_prev", "net_ma3", "st_net",
                 "st_min_rel", "st_ing", "st_gas", "dias_a_15", "dias_a_fin", "grati_h", "navidad_h", "escolar_h", "feriados_h", "mes_sin", "mes_cos"] + CAT_DECL + [
                 "personas_a_cargo", "colchon_meses", "paga_en_usd", "cuota_rel"]
FEATURES_EVENTO = ["ev_ahora", "ev_horizonte"]


def cortes(df: pd.DataFrame, fechas: dict) -> dict:
    """Particiones temporales con embargo: un origen de entrenamiento cuyo horizonte toca la ventana siguiente se descarta."""
    f = df["fecha"]
    emb = pd.Timedelta(days=H)
    t_fin, c_ini, c_fin = pd.Timestamp(fechas["entrena_hasta"]), pd.Timestamp(fechas["calibra_desde"]), pd.Timestamp(fechas["prueba_desde"])
    return {"entrena": df[f <= t_fin - emb], "ajusta": df[(f >= t_fin + pd.Timedelta(days=1)) & (f < c_ini - emb)], "calibra": df[(f >= c_ini) & (f < c_fin - emb)],
            "prueba": df[f >= c_fin]}


def pinball(y, q, alpha):
    d = y - q
    return float(np.mean(np.maximum(alpha * d, (alpha - 1) * d)))


def entrenar_cuantil(X, y, alpha, params=None, X_val=None, y_val=None):
    p = {**PARAMS_BASE, **(params or {})}
    m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, **p)
    kw = {}
    if X_val is not None:
        kw = dict(eval_X=X_val, eval_y=y_val, callbacks=[lgb.early_stopping(40, verbose=False)])
    return m.fit(X, y, **kw)


class Pronosticador:
    """Cuantiles 10/50/90 del flujo neto normalizado, conformal por segmento y clasificador calibrado de rojo."""

    def __init__(self, features, params=None, alfa=0.2, por_segmento=False):
        self.features, self.params, self.alfa, self.por_segmento = list(features), params or {}, alfa, por_segmento

    def ajustar(self, ent, ajus, cal):
        X, Xv, Xc = ent[self.features], ajus[self.features], cal[self.features]
        self.modelos = {}
        for a in (0.1, 0.5, 0.9):
            self.modelos[a] = entrenar_cuantil(X, ent["y_net_n"], a, self.params, Xv, ajus["y_net_n"])
        q = {a: self.modelos[a].predict(Xc) for a in self.modelos}
        e = np.maximum(q[0.1] - cal["y_net_n"].to_numpy(), cal["y_net_n"].to_numpy() - q[0.9])
        self.q_global = self._cuantil_conformal(e)
        self.q_seg = {int(s): self._cuantil_conformal(e[(cal["segmento"] == s).to_numpy()]) for s in cal["segmento"].unique() if (cal["segmento"] == s).sum() >= 200}
        clf = lgb.LGBMClassifier(**{**PARAMS_BASE, **self.params, "n_estimators": 300}).fit(X, ent["rojo30"])
        self.clf = clf
        self.iso = IsotonicRegression(out_of_bounds="clip").fit(clf.predict_proba(Xc)[:, 1], cal["rojo30"])
        pos = ent["rojo30"] == 1
        self.dia = lgb.LGBMRegressor(objective="l1", **{**PARAMS_BASE, **self.params, "n_estimators": 300}).fit(X[pos], ent.loc[pos, "y_dia"])
        return self

    def _cuantil_conformal(self, e):
        n = len(e)
        return float(np.quantile(e, min(np.ceil((n + 1) * (1 - self.alfa)) / n, 1.0)))

    def predecir(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df[self.features]
        q = {a: self.modelos[a].predict(X) for a in self.modelos}
        qs = np.array([self.q_seg.get(int(s), self.q_global) if self.por_segmento else self.q_global for s in df["segmento"]])
        lo, hi = q[0.1] - qs, q[0.9] + qs
        esc = df["escala"].to_numpy()
        base = df["saldo_t"].to_numpy()
        out = pd.DataFrame({"saldo_esperado": base + q[0.5] * esc, "saldo_bajo": base + lo * esc, "saldo_alto": base + hi * esc, "ancho_rel": (hi - lo),
                            "p_rojo": self.iso.predict(self.clf.predict_proba(X)[:, 1])}, index=df.index)
        out["dia_riesgo"] = np.clip(np.round(self.dia.predict(X)), 1, H)
        return out


def metricas(df: pd.DataFrame, pred: pd.DataFrame) -> dict:
    y = df["y_saldo"].to_numpy()
    err = np.abs(pred["saldo_esperado"].to_numpy() - y)
    esc = df["escala"].to_numpy()
    dentro = (y >= pred["saldo_bajo"].to_numpy()) & (y <= pred["saldo_alto"].to_numpy())
    return {"mae_s": float(err.mean()), "mae_rel_ingreso": float((err / esc).mean()), "mape_acotado": float((err / np.maximum(np.abs(y), 0.25 * esc)).mean()),
            "cobertura_80": float(dentro.mean()), "ancho_rel": float(((pred["saldo_alto"] - pred["saldo_bajo"]).to_numpy() / esc).mean())}


def baseline_ma3(df: pd.DataFrame, q_resid: tuple) -> pd.DataFrame:
    """Plan: promedio movil de 3 meses. Banda con cuantiles de residuos de calibracion (en unidades normalizadas)."""
    base, esc = df["saldo_t"].to_numpy(), df["escala"].to_numpy()
    mu = df["net_ma3"].to_numpy()
    return pd.DataFrame({"saldo_esperado": base + mu * esc, "saldo_bajo": base + (mu + q_resid[0]) * esc, "saldo_alto": base + (mu + q_resid[1]) * esc}, index=df.index)


def baseline_estructural(df: pd.DataFrame, q_resid: tuple) -> pd.DataFrame:
    base, esc = df["saldo_t"].to_numpy(), df["escala"].to_numpy()
    mu = df["st_net"].to_numpy()
    return pd.DataFrame({"saldo_esperado": base + mu * esc, "saldo_bajo": base + (mu + q_resid[0]) * esc, "saldo_alto": base + (mu + q_resid[1]) * esc}, index=df.index)


def cuantiles_residuo(cal: pd.DataFrame, columna: str, alfa: float = 0.2) -> tuple:
    r = cal["y_net_n"].to_numpy() - cal[columna].to_numpy()
    return float(np.quantile(r, alfa / 2)), float(np.quantile(r, 1 - alfa / 2))


def metricas_rojo(y, score) -> dict:
    p = np.clip(score, 0, 1)
    bins = np.minimum((p * 10).astype(int), 9)
    ece = sum(abs(p[bins == b].mean() - y[bins == b].mean()) * (bins == b).mean() for b in range(10) if (bins == b).any())
    return {"pr_auc": float(average_precision_score(y, score)), "roc_auc": float(roc_auc_score(y, score)), "brier": float(brier_score_loss(y, p)), "ece": float(ece)}


def dia_de_riesgo_aciertos(df: pd.DataFrame, dia_pred: np.ndarray, tol: int = 3) -> dict:
    """Entre los origenes que de verdad caen en rojo: error medio en dias y fraccion dentro de +-tol dias. Sin prediccion cuenta como 31."""
    m = df["y_dia"].to_numpy() > 0
    d = np.minimum(dia_pred[m], H + 1)
    err = np.abs(d - df["y_dia"].to_numpy()[m])
    return {"n": int(m.sum()), "mae_dias": float(err.mean()), "acierto_pm3": float((err <= tol).mean())}


def guardar(obj: dict, nombre: str) -> str:
    os.makedirs(MODELOS, exist_ok=True)
    obj["manifiesto"] = {"python": platform.python_version(), "lightgbm": lgb.__version__, "numpy": np.__version__, "pandas": pd.__version__}
    ruta = os.path.join(MODELOS, f"{nombre}.pkl")
    joblib.dump(obj, ruta, compress=3)
    return ruta


def optimizar(ent: pd.DataFrame, ajus: pd.DataFrame, features, n_trials: int = 20, timeout: int = 300, semilla: int = 0) -> dict:
    """Busca hiperparametros del cuantil 0,5 minimizando la perdida pinball en la ventana de ajuste (posterior al entrenamiento)."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objetivo(trial):
        params = {"learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True), "num_leaves": trial.suggest_int("num_leaves", 15, 127),
                  "min_child_samples": trial.suggest_int("min_child_samples", 20, 200), "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                  "subsample": trial.suggest_float("subsample", 0.5, 1.0), "reg_lambda": trial.suggest_float("reg_lambda", 1e-2, 20, log=True)}
        m = entrenar_cuantil(ent[features], ent["y_net_n"], 0.5, params, ajus[features], ajus["y_net_n"])
        return pinball(ajus["y_net_n"].to_numpy(), m.predict(ajus[features]), 0.5)

    estudio = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=semilla))
    estudio.optimize(objetivo, n_trials=n_trials, timeout=timeout)
    return {**estudio.best_params, "_mejor_pinball": estudio.best_value, "_n_trials": len(estudio.trials)}
