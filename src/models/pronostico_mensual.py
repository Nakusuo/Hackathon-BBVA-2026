"""Proyeccion por meses (1 a 6): cuanto ingresara, cuanto gastara y cuanto le quedaria al cliente, con rango al 80 %.
Modelo directo por horizonte con LightGBM cuantilico, conformal por horizonte, frente a mismo mes del anio anterior y promedio de 3 meses."""
import numpy as np
import pandas as pd
import lightgbm as lgb

from src.models import datos
from src.models.pronostico import CAT_DECL, PARAMS_BASE

HMAX = 6
OBJETIVOS = ("ing", "gas", "net")
GASTOS = ["gasto_fijo", "gasto_variable", "gasto_hormiga", "gasto_deuda"]
INGRESOS = ["ingreso_operativo", "ingreso_extraordinario"]
FEATURES = ["h", "escala", "ing0", "ing1", "ing2", "ing5", "ing11", "gas0", "gas1", "gas2", "gas5", "gas11", "ing_m3", "ing_m6", "ing_m12", "gas_m3", "gas_m6", "gas_m12", "cv_ing6", "cv_gas6",
            "ing_mismo_mes_anio_prev", "gas_mismo_mes_anio_prev", "saldo_rel", "rojo3", "mes_objetivo_sin", "mes_objetivo_cos", "grati_objetivo", "escolar_objetivo", "navidad_objetivo",
            "ev_origen", "ev_objetivo", "ipc_rel_origen"] + CAT_DECL + ["personas_a_cargo", "colchon_meses", "paga_en_usd", "cuota_rel", "segmento"]


def panel_arrays(carpeta: str) -> dict:
    p = datos.cargar_panel(carpeta)
    ids = np.array(sorted(p["customer_id"].unique()))
    meses = pd.PeriodIndex(sorted(p["mes"].unique()), freq="M")
    pos_c = pd.Series(np.arange(len(ids)), index=ids)
    pos_m = pd.Series(np.arange(len(meses)), index=meses.astype(str))
    c, m = p["customer_id"].map(pos_c).to_numpy(), p["mes"].map(pos_m).to_numpy()
    B, M = len(ids), len(meses)

    def arr(col):
        a = np.zeros((B, M), np.float64)
        a[c, m] = p[col].to_numpy(dtype=float)
        return a
    ing = arr("ingreso_operativo") + arr("ingreso_extraordinario")
    gas = sum(arr(g) for g in GASTOS)
    return {"ids": ids, "meses": meses, "ing": ing, "gas": gas, "saldo_fin": arr("saldo_fin"), "rojo": arr("dias_en_rojo")}


def construir_filas(carpeta: str, clientes: pd.DataFrame, seg_map: dict, con_objetivo: bool = True, origenes=None) -> pd.DataFrame:
    A = panel_arrays(carpeta)
    ing, gas, ids, meses = A["ing"], A["gas"], A["ids"], A["meses"]
    B, M = ing.shape
    ctx = datos.cargar_contexto(carpeta)
    ev_cols = [c for c in ctx.columns if c.startswith("fuerza_")]
    ev_dia = ctx[ev_cols].max(axis=1).to_numpy() if ev_cols else np.zeros(len(ctx))
    ev_mes = pd.Series(ev_dia, index=pd.DatetimeIndex(ctx["fecha"])).groupby(pd.DatetimeIndex(ctx["fecha"]).to_period("M")).mean().reindex(meses).fillna(0).to_numpy()
    macro = datos.cargar_macro(carpeta).set_index("mes")["ipc_relativo"].reindex(meses.astype(str)).to_numpy()
    cl = clientes.reindex(ids)
    cat = {c: cl[c].astype("category").cat.codes.to_numpy() for c in CAT_DECL}
    seg = np.array([seg_map.get(i, -1) for i in ids])
    cs_i, cs_g = np.concatenate([np.zeros((B, 1)), np.cumsum(ing, 1)], 1), np.concatenate([np.zeros((B, 1)), np.cumsum(gas, 1)], 1)
    cs_r = np.concatenate([np.zeros((B, 1)), np.cumsum(A["rojo"], 1)], 1)
    mes_num = np.array([p.month for p in meses])
    filas = []
    for t in (origenes if origenes is not None else range(12, M - 1)):
        def m(cs, w):
            return (cs[:, t + 1] - cs[:, t + 1 - w]) / w
        ing6, gas6 = m(cs_i, 6), m(cs_g, 6)
        escala = np.maximum(ing6, 200.0)
        cv_i = ing[:, t - 5:t + 1].std(1) / np.maximum(ing[:, t - 5:t + 1].mean(1), 1.0)
        cv_g = gas[:, t - 5:t + 1].std(1) / np.maximum(gas[:, t - 5:t + 1].mean(1), 1.0)
        for h in range(1, HMAX + 1):
            if con_objetivo and t + h >= M:
                break
            tm = (mes_num[t] + h - 1) % 12 + 1
            ly = t + h - 12
            base = {"cliente_idx": np.arange(B), "t": t, "h": h, "escala": escala, "ing0": ing[:, t] / escala, "ing1": ing[:, t - 1] / escala, "ing2": ing[:, t - 2] / escala, "ing5": ing[:, t - 5] / escala,
                    "ing11": ing[:, t - 11] / escala, "gas0": gas[:, t] / escala, "gas1": gas[:, t - 1] / escala, "gas2": gas[:, t - 2] / escala, "gas5": gas[:, t - 5] / escala, "gas11": gas[:, t - 11] / escala,
                    "ing_m3": m(cs_i, 3) / escala, "ing_m6": ing6 / escala, "ing_m12": m(cs_i, 12) / escala, "gas_m3": m(cs_g, 3) / escala, "gas_m6": gas6 / escala, "gas_m12": m(cs_g, 12) / escala,
                    "cv_ing6": cv_i, "cv_gas6": cv_g, "ing_mismo_mes_anio_prev": (ing[:, ly] / escala) if ly >= 0 else np.nan, "gas_mismo_mes_anio_prev": (gas[:, ly] / escala) if ly >= 0 else np.nan,
                    "saldo_rel": A["saldo_fin"][:, t] / escala, "rojo3": cs_r[:, t + 1] - cs_r[:, t - 2], "mes_objetivo_sin": np.sin(2 * np.pi * tm / 12), "mes_objetivo_cos": np.cos(2 * np.pi * tm / 12),
                    "grati_objetivo": float(tm in (7, 12)), "escolar_objetivo": float(tm == 3), "navidad_objetivo": float(tm == 12), "ev_origen": ev_mes[t],
                    "ev_objetivo": ev_mes[min(t + h, M - 1)], "ipc_rel_origen": macro[t], "personas_a_cargo": cl["personas_a_cargo"].to_numpy(), "colchon_meses": cl["colchon_meses"].to_numpy(),
                    "paga_en_usd": cl["paga_en_usd"].astype(int).to_numpy(), "segmento": seg, **cat}
            base["cuota_rel"] = cl["cuota_mensual"].to_numpy() / escala
            if not con_objetivo:
                base["mes_objetivo"] = str(meses[t] + h)
            if con_objetivo:
                base.update({"y_ing": ing[:, t + h] / escala, "y_gas": gas[:, t + h] / escala, "y_net": (ing[:, t + h] - gas[:, t + h]) / escala, "mes_objetivo": str(meses[t + h])})
            filas.append(pd.DataFrame(base))
    df = pd.concat(filas, ignore_index=True)
    df["mes_origen"] = meses[df["t"].to_numpy()].astype(str)
    df["fecha_origen"] = meses[df["t"].to_numpy()].to_timestamp(how="end").normalize()
    return df


def cortes(df: pd.DataFrame, entrena_hasta="2022-06-30", ajusta=("2022-10-01", "2023-03-31"), calibra=("2023-04-01", "2023-06-30"), prueba_desde="2024-01-01") -> dict:
    """Ventanas por mes de origen. La calibracion termina 6 meses antes de la prueba (el horizonte maximo), de modo que ningun objetivo de calibracion
    cae dentro del periodo de prueba. Entrenamiento y ajuste (solo para parar el entrenamiento) comparten 3 meses de objetivos: se declara en la evaluacion."""
    f = df["fecha_origen"]
    return {"entrena": df[f <= pd.Timestamp(entrena_hasta)], "ajusta": df[(f >= pd.Timestamp(ajusta[0])) & (f <= pd.Timestamp(ajusta[1]))],
            "calibra": df[(f >= pd.Timestamp(calibra[0])) & (f <= pd.Timestamp(calibra[1]))], "prueba": df[f >= pd.Timestamp(prueba_desde)]}


class Mensual:
    def __init__(self, features=FEATURES, params=None, alfa=0.2):
        self.features, self.params, self.alfa = list(features), params or {}, alfa

    def ajustar(self, ent, ajus, cal):
        p = {**PARAMS_BASE, **self.params, "n_estimators": 400}
        self.m, self.q = {}, {}
        for o in OBJETIVOS:
            for a in (0.1, 0.5, 0.9):
                mod = lgb.LGBMRegressor(objective="quantile", alpha=a, **p)
                self.m[(o, a)] = mod.fit(ent[self.features], ent[f"y_{o}"], eval_X=ajus[self.features], eval_y=ajus[f"y_{o}"], callbacks=[lgb.early_stopping(40, verbose=False)])
            lo, hi = self.m[(o, 0.1)].predict(cal[self.features]), self.m[(o, 0.9)].predict(cal[self.features])
            e = np.maximum(lo - cal[f"y_{o}"].to_numpy(), cal[f"y_{o}"].to_numpy() - hi)
            for h in range(1, HMAX + 1):
                mh = (cal["h"] == h).to_numpy()
                self.q[(o, h, -1)] = self._cuantil(e[mh], e)
                for g in cal["tipo_trabajo"].unique():  # conformal por tipo de trabajo (Mondrian): bandas anchas para ingreso irregular, estrechas para estable
                    mg = mh & (cal["tipo_trabajo"] == g).to_numpy()
                    self.q[(o, h, int(g))] = self._cuantil(e[mg], e[mh]) if mg.sum() >= 80 else self.q[(o, h, -1)]
        return self

    def predecir_recalibrado(self, todo: pd.DataFrame, prueba: pd.DataFrame, ventana=(11, 6)) -> pd.DataFrame:
        """Recalibracion continua: el q de cada mes de origen sale de los residuos de origenes entre t-11 y t-6 meses, los unicos con objetivo ya conocido
        (el horizonte maximo es 6). Es lo que haria el sistema en produccion, sin usar nada del futuro."""
        F = self.features
        crudo = {(o, a): self.m[(o, a)].predict(todo[F]) for o in OBJETIVOS for a in (0.1, 0.5, 0.9)}
        err = {o: np.maximum(crudo[(o, 0.1)] - todo[f"y_{o}"].to_numpy(), todo[f"y_{o}"].to_numpy() - crudo[(o, 0.9)]) for o in OBJETIVOS}
        out = {f"{o}_{k}": np.zeros(len(prueba)) for o in OBJETIVOS for k in ("esperado", "bajo", "alto")}
        t_todo, h_todo, g_todo = todo["t"].to_numpy(), todo["h"].to_numpy(), todo["tipo_trabajo"].to_numpy()
        pos = pd.Series(np.arange(len(todo)), index=todo.index)
        for t in np.sort(prueba["t"].unique()):
            en_ventana = (t_todo >= t - ventana[0]) & (t_todo <= t - ventana[1])
            filas_t = np.flatnonzero((prueba["t"] == t).to_numpy())
            idx_todo = pos.loc[prueba.index[filas_t]].to_numpy()
            for o in OBJETIVOS:
                q = np.empty(len(filas_t))
                for j, (h, g) in enumerate(zip(h_todo[idx_todo], g_todo[idx_todo])):
                    m_g = en_ventana & (h_todo == h) & (g_todo == g)
                    m_h = en_ventana & (h_todo == h)
                    q[j] = self._cuantil(err[o][m_g], err[o][m_h] if m_h.sum() > 30 else err[o]) if m_h.any() else self.q[(o, int(h), -1)]
                esc = prueba["escala"].to_numpy()[filas_t]
                out[f"{o}_esperado"][filas_t] = crudo[(o, 0.5)][idx_todo] * esc
                out[f"{o}_bajo"][filas_t] = (crudo[(o, 0.1)][idx_todo] - q) * esc
                out[f"{o}_alto"][filas_t] = (crudo[(o, 0.9)][idx_todo] + q) * esc
        return pd.DataFrame(out, index=prueba.index)

    def _cuantil(self, e, respaldo):
        e = e if len(e) > 30 else respaldo
        n = len(e)
        return float(np.quantile(e, min(np.ceil((n + 1) * (1 - self.alfa)) / n, 1.0)))

    def predecir(self, df: pd.DataFrame) -> pd.DataFrame:
        out = {}
        esc = df["escala"].to_numpy()
        for o in OBJETIVOS:
            q = np.array([self.q.get((o, int(h), int(g)), self.q[(o, int(h), -1)]) for h, g in zip(df["h"], df["tipo_trabajo"])])
            out[f"{o}_esperado"] = self.m[(o, 0.5)].predict(df[self.features]) * esc
            out[f"{o}_bajo"] = (self.m[(o, 0.1)].predict(df[self.features]) - q) * esc
            out[f"{o}_alto"] = (self.m[(o, 0.9)].predict(df[self.features]) + q) * esc
        return pd.DataFrame(out, index=df.index)


def baselines(df: pd.DataFrame, cal: pd.DataFrame) -> dict:
    """Mismo mes del anio anterior (o ultimo valor si no hay) y promedio de 3 meses, con banda de residuos de la calibracion por horizonte."""
    def pred(base_col_i, base_col_g):
        return {"ing": df[base_col_i].fillna(df["ing_m3"]).to_numpy(), "gas": df[base_col_g].fillna(df["gas_m3"]).to_numpy()}

    def residuos(cal_i, cal_g):
        r = {}
        for o, ci in (("ing", cal_i["ing"]), ("gas", cal_i["gas"])):
            e = cal[f"y_{o}"].to_numpy() - ci
            r[o] = {h: (np.quantile(e[(cal["h"] == h).to_numpy()], 0.1), np.quantile(e[(cal["h"] == h).to_numpy()], 0.9)) for h in range(1, HMAX + 1)}
        return r
    sal = {}
    for nombre, (ci, cg) in {"mismo_mes_anio_previo": ("ing_mismo_mes_anio_prev", "gas_mismo_mes_anio_prev"), "promedio_3_meses": ("ing_m3", "gas_m3")}.items():
        pc = {"ing": cal[ci].fillna(cal["ing_m3"]).to_numpy(), "gas": cal[cg].fillna(cal["gas_m3"]).to_numpy()}
        rr = residuos(pc, pc)
        pt = pred(ci, cg)
        esc = df["escala"].to_numpy()
        d = {}
        for o in ("ing", "gas"):
            lo = np.array([rr[o][int(h)][0] for h in df["h"]])
            hi = np.array([rr[o][int(h)][1] for h in df["h"]])
            d[f"{o}_esperado"], d[f"{o}_bajo"], d[f"{o}_alto"] = pt[o] * esc, (pt[o] + lo) * esc, (pt[o] + hi) * esc
        d["net_esperado"], d["net_bajo"], d["net_alto"] = d["ing_esperado"] - d["gas_esperado"], d["ing_bajo"] - d["gas_alto"], d["ing_alto"] - d["gas_bajo"]
        sal[nombre] = pd.DataFrame(d, index=df.index)
    return sal


def metricas(df: pd.DataFrame, pred: pd.DataFrame, por: str = "h") -> pd.DataFrame:
    filas = {}
    esc = df["escala"].to_numpy()
    for g, idx in df.groupby(por).groups.items():
        i = df.index.get_indexer(idx)
        fila = {"n": len(i)}
        for o in OBJETIVOS:
            y = df[f"y_{o}"].to_numpy()[i] * esc[i]
            e = np.abs(pred[f"{o}_esperado"].to_numpy()[i] - y)
            fila[f"{o}_mae_rel"] = float((e / esc[i]).mean())
            fila[f"{o}_wape"] = float(e.sum() / max(np.abs(y).sum(), 1.0))
            fila[f"{o}_cobertura"] = float(((y >= pred[f"{o}_bajo"].to_numpy()[i]) & (y <= pred[f"{o}_alto"].to_numpy()[i])).mean())
        filas[g] = fila
    return pd.DataFrame(filas).T
