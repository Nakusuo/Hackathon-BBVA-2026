"""Simulador por lotes de clientes. Genera mes a mes con todos los clientes del lote en paralelo (numpy),
de modo que el saldo de un mes condiciona el gasto del siguiente y los eventos mueven ingresos y consumo."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.generador import catalogo as K
from src.generador.contexto import Contexto

SEG = {s: i for i, s in enumerate(K.SEGMENTOS)}
REG = {r: i for i, r in enumerate(K.REGIONES)}
S_FORMAL, S_COMISION, S_DIARIO, S_PROYECTOS, S_MIXTO = range(5)
FIJO_SHARE = np.array([1.0, 0.6, 0.0, 0.0, 0.5])
LAM_DIARIO, LAM_PROY, LAM_MIXTO = 2.0, 3.0, 1.5
DOW_ING = np.array([.95, .95, .95, 1, 1.1, 1.25, .8])
SEAS_ING = np.array([.95, .92, .98, 1, 1.03, 1, 1.08, 1, 1, 1, 1.05, 1.25])
PRECIO_SUBS = np.array([29.9, 19.9, 24.9, 34.9, 12.9])
DISCRECIONAL = np.array([v["nombre"] in {"delivery", "restaurantes", "snacks", "ocio", "compras"} for v in K.VARIABLES])
LAB_SUB_DUP = 1
LAB_ATIPICO = 2

_MAXCOM = max(len(v["comercios"]) for v in K.VARIABLES)
COM_TAB = np.zeros((K.N_VAR, _MAXCOM), dtype=np.int16)
COM_N = np.zeros(K.N_VAR, dtype=int)
for _i, _v in enumerate(K.VARIABLES):
    _ids = [K.ID_COMERCIO[c] for c in _v["comercios"]]
    COM_TAB[_i, :len(_ids)] = _ids
    COM_N[_i] = len(_ids)
COM_GLOB = {cid: np.array([K.ID_COMERCIO[c] for c in K.COMERCIOS_DE_CAT[n]], dtype=np.int16) for cid, n in enumerate(K.NOMBRES_CAT)}
C = K.ID_CAT


class _Filas:
    CAMPOS = ("b", "day", "secs", "monto", "moneda", "pen", "ing", "cat", "com", "lab")

    def __init__(self):
        self.d = {k: [] for k in self.CAMPOS}

    def add(self, b, day, secs, monto, pen, ing, cat, com, moneda=0, lab=0):
        b = np.atleast_1d(b)
        n = len(b)
        if n == 0:
            return
        for k, v, t in (("b", b, np.int32), ("day", day, np.int32), ("secs", secs, np.int32), ("monto", monto, np.float32),
                        ("pen", pen, np.float32), ("ing", ing, bool), ("cat", cat, np.int16), ("com", com, np.int16),
                        ("moneda", moneda, np.int8), ("lab", lab, np.int8)):
            self.d[k].append(np.broadcast_to(np.asarray(v, dtype=t), (n,)).copy())

    def concat(self):
        return {k: (np.concatenate(v) if v else np.empty(0)) for k, v in self.d.items()}


def _secs(rng, n, h0, h1):
    return rng.integers(h0 * 3600, h1 * 3600, n, dtype=np.int64).astype(np.int32)


def _com_aleatorio(rng, cat, n):
    lista = COM_GLOB[cat]
    return lista[rng.integers(0, len(lista), n)]


@dataclass
class ResultadoLote:
    filas: dict
    ing_dia: np.ndarray
    gas_dia: np.ndarray
    saldo_cierre: np.ndarray
    mult_ing: np.ndarray


def _multiplicadores(cl, ctx: Contexto, rng):
    B, D = len(cl), ctx.n_dias
    seg = cl["segmento"].map(SEG).to_numpy()
    reg = cl["region"].map(REG).to_numpy()
    mult_ing = np.ones((B, D), dtype=np.float32)
    mult_tasa = np.ones((B, K.N_VAR, D), dtype=np.float32)
    mult_precio = np.ones((B, K.N_VAR, D), dtype=np.float32)
    for k, ev in enumerate(ctx.eventos):
        f = ctx.fuerza[k]
        if not f.any():
            continue
        sm = np.array([ev.get("ingreso", {}).get(s, 1.0) for s in K.SEGMENTOS])[seg]
        pc = np.array([ev.get("prob_corte_total", {}).get(s, 0.0) for s in K.SEGMENTOS])[seg]
        sv = np.array([ev.get("severidad_region", {}).get(r, 1.0) for r in K.REGIONES])[reg]
        efecto = (f[None, :] * sv[:, None]).astype(np.float32)
        corte = rng.random(B) < pc * sv
        fac = np.where(corte[:, None], 1 - 0.95 * efecto, 1 + (sm[:, None] - 1) * efecto)
        mult_ing *= fac.astype(np.float32)
        km = np.array([ev.get("categorias", {}).get(v["nombre"], 1.0) for v in K.VARIABLES])
        pm = np.array([ev.get("precio_categorias", {}).get(v["nombre"], 1.0) for v in K.VARIABLES])
        mult_tasa *= (1 + (km[None, :, None] - 1) * efecto[:, None, :]).astype(np.float32)
        mult_precio *= (1 + (pm[None, :, None] - 1) * efecto[:, None, :]).astype(np.float32)
    return mult_ing, mult_tasa, mult_precio


def _shocks(cl, ctx: Contexto, rng):
    """Para cada shock: dia y monto por cliente (dia = -1 si no lo recibe)."""
    B = len(cl)
    seg = cl["segmento"].map(SEG).to_numpy()
    out = []
    for s in ctx.shocks:
        f0 = pd.Timestamp(s["fecha"])
        if f0 > ctx.fechas[-1] or f0 + pd.Timedelta(days=s["ventana_dias"]) < ctx.fechas[0]:
            continue
        prob = np.array([s["elegibles"].get(sg, 0.0) for sg in K.SEGMENTOS])[seg]
        recibe = rng.random(B) < prob
        dia = (f0 - ctx.fechas[0]).days + rng.integers(0, s["ventana_dias"] + 1, B)
        dia = np.where(recibe & (dia >= 0) & (dia < ctx.n_dias), dia, -1)
        mo = s["monto"]
        monto = np.minimum(rng.lognormal(np.log(mo["mediana"]), mo["sigma"], B) if mo["sigma"] > 0 else np.full(B, mo["mediana"]), mo["tope"])
        out.append((C[s["categoria"]], dia, monto))
    return out


def simular_lote(cl: pd.DataFrame, ctx: Contexto, rng: np.random.Generator, p_atipico: float = 0.003) -> ResultadoLote:
    B, D, M = len(cl), ctx.n_dias, ctx.n_meses
    seg = cl["segmento"].map(SEG).to_numpy()
    ing_obs = (cl["ingreso_base"] * (1 - cl["fraccion_efectivo"])).to_numpy()
    pas = cl["traspaso_inflacion"].to_numpy()
    r_gasto = cl["gasto_ratio"].to_numpy()
    s_ahorro = cl["ahorro_tasa"].to_numpy()
    mucho = (cl["perfil_gasto_real"] == "gasta_mucho").to_numpy()
    planilla = cl["planilla"].to_numpy()
    fijo_eff = FIJO_SHARE[seg] * planilla
    dia_cambio = np.where(cl["cambio_patron"], (cl["pos_cambio_patron"].fillna(0) * D), D + 10).astype(int)
    f_cambio = cl["factor_cambio_ingreso"].to_numpy()
    saldo = cl["saldo_inicial"].to_numpy().astype(float).copy()
    saldo_ini = saldo.copy()
    bolsillo = cl["ahorro_inicial"].to_numpy().astype(float).copy()
    acceso = cl["acceso_credito_informal"].to_numpy()
    tasa_inf = cl["tasa_credito_informal"].to_numpy()
    usd = cl["paga_en_usd"].to_numpy()
    mult_ing, mult_tasa, mult_precio = _multiplicadores(cl, ctx, rng)
    shocks = _shocks(cl, ctx, rng)
    emp = rng.integers(0, 5, B)

    # --- compromisos fijos (valores reales a precios de 2025-12)
    alq_real = cl["alquiler_share"].to_numpy() * ing_obs
    luz_real = ing_obs * rng.uniform(0.025, 0.045, B)
    agua_real = ing_obs * rng.uniform(0.010, 0.020, B)
    int_real = rng.uniform(55, 120, B) * (rng.random(B) < 0.75)
    cel_real = rng.uniform(30, 80, B)
    cuota_real = cl["cuota_share"].to_numpy() * ing_obs
    cuota_ini = np.where(rng.random(B) < 0.3, rng.integers(0, max(1, M // 2), B), 0)
    cuota_fin = np.where(rng.random(B) < 0.25, cuota_ini + rng.integers(6, max(7, M), B), M + 5)
    edad_ok = cl["rango_edad"].isin(["25-34", "35-44", "45-54"]).to_numpy()
    colegio_real = np.where((cl["personas_a_cargo"].to_numpy() > 0) & edad_ok & (rng.random(B) < 0.6), ing_obs * rng.uniform(0.05, 0.12, B), 0.0)
    seguro_real = np.where(rng.random(B) < 0.25, rng.uniform(40, 120, B), 0.0)
    dias_fijo = {k: rng.integers(lo, hi + 1, B) for k, (lo, hi) in dict(alq=(1, 10), luz=(8, 20), agua=(8, 20), inte=(1, 28), cel=(1, 28), cuota=(1, 28), seg=(1, 28)).items()}
    n_subs = rng.choice(4, B, p=[.25, .35, .28, .12])
    sub_com = np.stack([rng.permutation(5)[:3] for _ in range(B)])
    dup = (n_subs >= 2) & (rng.random(B) < 0.18)
    sub_com[dup, 1] = sub_com[dup, 0]
    sub_amt = PRECIO_SUBS[sub_com] * rng.choice([1.0, 1.0, 1.15], (B, 3))
    sub_amt[dup, 1] = sub_amt[dup, 0]
    sub_day = rng.integers(1, 29, (B, 3))
    sub_day[dup, 1] = (sub_day[dup, 0] + rng.integers(5, 15, int(dup.sum())) - 1) % 28 + 1
    sub_ini = np.where(np.arange(3)[None, :] == 0, rng.integers(0, M // 3 + 1, (B, 1)), rng.integers(0, M, (B, 3)))
    sub_ini[dup, 1] = np.minimum(sub_ini[dup, 0] + rng.integers(1, max(2, M // 2), int(dup.sum())), M - 1)
    sub_fin = np.where(rng.random((B, 3)) < 0.25, sub_ini + rng.integers(3, max(4, M // 2), (B, 3)), M + 5)
    sub_activa = np.arange(3)[None, :] < n_subs[:, None]
    fijo_real_total = alq_real + luz_real + agua_real + int_real + cel_real + cuota_real + colegio_real * 10 / 12 + seguro_real + (sub_amt * sub_activa).sum(1)

    # --- presupuesto variable y tasas por categoria
    var_real = np.maximum(r_gasto * ing_obs - fijo_real_total, 0.15 * ing_obs)
    pesos = np.array([v["peso"] for v in K.VARIABLES])[None, :] * np.where(mucho[:, None], np.array([v["mucho"] for v in K.VARIABLES])[None, :], 1.0)
    pesos = pesos / pesos.sum(1, keepdims=True)
    tasa_bc = np.array([v["tasa"] for v in K.VARIABLES])[None, :] * cl["heterogeneidad_consumo"].to_numpy()[:, None] * rng.lognormal(0, 0.15, (B, K.N_VAR))
    monto_tipico = var_real[:, None] * pesos / (tasa_bc * 30.4)
    sigma_c = np.array([v["sigma"] for v in K.VARIABLES])
    fav = rng.integers(0, 6, (B, K.N_VAR, 3)) % COM_N[None, :, None]
    dow_c = np.array([v["dow"] for v in K.VARIABLES])
    seas_c = np.array([v["estacion"] for v in K.VARIABLES])

    ene_mes = np.array([int(np.flatnonzero(ctx.meses.year == y)[0]) for y in ctx.meses.year])
    pend: dict[int, list] = {}
    F = _Filas()
    ing_dia = np.zeros((B, D), dtype=np.float32)
    gas_dia = np.zeros((B, D), dtype=np.float32)

    for m in range(M):
        d0, d1 = ctx.ini_mes[m], ctx.fin_mes[m]
        dm = d1 - d0 + 1
        mes = ctx.mes_cal[d0]
        ipc = ctx.ipc_rel[m]
        base_nom = ing_obs * ipc ** pas * np.where(d0 + 14 >= dia_cambio, f_cambio, 1.0)
        FM = _Filas()
        mi_mid = mult_ing[:, d0 + dm // 2]

        # 1. ingresos fijos por planilla
        for dia_pago, parte, sel in ((ctx.pago_15[m], 0.5, seg == S_FORMAL), (ctx.pago_fin[m], None, planilla & (FIJO_SHARE[seg] > 0))):
            b = np.flatnonzero(sel)
            if b.size == 0:
                continue
            monto = base_nom[b] * (parte if parte else np.where(seg[b] == S_FORMAL, 0.5, FIJO_SHARE[seg[b]]))
            monto = monto * mult_ing[b, dia_pago] * (1 + rng.normal(0, 0.01, b.size))
            FM.add(b, dia_pago, _secs(rng, b.size, 6, 9), monto, monto, True, C["sueldo"], COM_GLOB[C["sueldo"]][emp[b] % len(COM_GLOB[C["sueldo"]])])
        # gratificacion
        if mes in (7, 12):
            b = np.flatnonzero(fijo_eff > 0)
            monto = base_nom[b] * fijo_eff[b] * mult_ing[b, ctx.pago_15[m]]
            FM.add(b, ctx.pago_15[m], _secs(rng, b.size, 6, 9), monto, monto, True, C["gratificacion"], _com_aleatorio(rng, C["gratificacion"], b.size))
        # 2. comisiones
        b = np.flatnonzero(seg == S_COMISION)
        if b.size:
            sea = {12: 1.3, 5: 1.15, 1: 0.85}.get(mes, 1.0)
            total = base_nom[b] * 0.4 * rng.lognormal(-0.06, 0.35, b.size) * sea * mi_mid[b]
            u = rng.uniform(0.3, 0.7, b.size)
            for frac, dia_loc in ((u, 9), (1 - u, 24)):
                dia = d0 + min(dia_loc, dm - 1)
                FM.add(b, dia, _secs(rng, b.size, 8, 18), total * frac, total * frac, True, C["comision"], _com_aleatorio(rng, C["comision"], b.size))
        # 3. cobros diarios del independiente de comercio o transporte
        b = np.flatnonzero(seg == S_DIARIO)
        if b.size:
            mi = mult_ing[np.ix_(b, np.arange(d0, d1 + 1))]
            vol_mes = rng.lognormal(0, 0.22, b.size)[:, None]
            lam = LAM_DIARIO * DOW_ING[ctx.dow[d0:d1 + 1]][None, :] * mi ** 0.6 * SEAS_ING[mes - 1] * vol_mes
            n = rng.poisson(lam)
            idx = np.repeat(np.arange(n.size), n.ravel())
            bi, di = np.unravel_index(idx, n.shape)
            bb = b[bi]
            media = base_nom[bb] / (LAM_DIARIO * 30.4) * mi[bi, di] ** 0.4 * vol_mes[bi, 0] ** 0.5
            monto = media * rng.lognormal(-0.18, 0.6, bb.size)
            FM.add(bb, d0 + di, _secs(rng, bb.size, 8, 21), monto, monto, True, C["venta_diaria"], _com_aleatorio(rng, C["venta_diaria"], bb.size))
        # 4. honorarios del independiente por proyectos y extra del mixto
        for sg, lam0, cat, parte in ((S_PROYECTOS, LAM_PROY, "honorarios", 1.0), (S_MIXTO, LAM_MIXTO, "ingreso_extra", None)):
            b = np.flatnonzero(seg == sg)
            if b.size == 0:
                continue
            n = rng.poisson(lam0 * mi_mid[b] ** 0.7)
            bb = np.repeat(b, n)
            if bb.size == 0:
                continue
            dia = d0 + rng.integers(0, dm, bb.size)
            share = 1.0 if parte else (1 - fijo_eff[bb])
            monto = base_nom[bb] * share / lam0 * mult_ing[bb, dia] ** 0.8 * rng.lognormal(-0.18, 0.6, bb.size)
            FM.add(bb, dia, _secs(rng, bb.size, 9, 19), monto, monto, True, C[cat], _com_aleatorio(rng, C[cat], bb.size))
        # 5. ingresos extraordinarios (bonos y retiros AFP)
        for cat, dia_s, monto_s in shocks:
            b = np.flatnonzero((dia_s >= d0) & (dia_s <= d1))
            FM.add(b, dia_s[b], _secs(rng, b.size, 8, 18), monto_s[b], monto_s[b], True, cat, _com_aleatorio(rng, cat, b.size))

        # 6. compromisos fijos
        def fijo(cat_nombre, monto_pen_arr, dia_loc, mask, h0=7, h1=12, lab=0, com=None):
            b = np.flatnonzero(mask & (monto_pen_arr > 0))
            if b.size == 0:
                return
            dia = d0 + np.minimum(dia_loc[b] - 1, dm - 1)
            cid = C[cat_nombre]
            FM.add(b, dia, _secs(rng, b.size, h0, h1), monto_pen_arr[b], monto_pen_arr[b], False, cid,
                   _com_aleatorio(rng, cid, b.size) if com is None else com[b], lab=lab)

        todos = np.ones(B, dtype=bool)
        alq_nom = alq_real * ctx.ipc_rel[ene_mes[m]]
        b_usd = np.flatnonzero(usd & (alq_real > 0))
        if b_usd.size:
            usd_monto = alq_real[b_usd] / ctx.fx[-1]
            pen = usd_monto * ctx.fx[m]
            FM.add(b_usd, d0 + np.minimum(dias_fijo["alq"][b_usd] - 1, dm - 1), _secs(rng, b_usd.size, 7, 12), usd_monto, pen, False,
                   C["alquiler"], _com_aleatorio(rng, C["alquiler"], b_usd.size), moneda=1)
        fijo("alquiler", alq_nom, dias_fijo["alq"], ~usd)
        fijo("luz", luz_real * ipc * (1.15 if mes in (1, 2, 3) else 1.0), dias_fijo["luz"], todos)
        fijo("agua", agua_real * ipc, dias_fijo["agua"], todos)
        fijo("internet", int_real * ipc ** 0.5, dias_fijo["inte"], todos)
        fijo("celular", cel_real * ipc ** 0.5, dias_fijo["cel"], todos)
        fijo("cuota_prestamo", cuota_real * ctx.ipc_rel[min(cuota_ini.max(), m)], dias_fijo["cuota"], (m >= cuota_ini) & (m <= cuota_fin))
        if mes >= 3:
            fijo("colegio", colegio_real * ipc, np.full(B, 5), todos)
        fijo("seguro", seguro_real * ipc ** 0.5, dias_fijo["seg"], todos)
        for j in range(3):
            act = sub_activa[:, j] & (m >= sub_ini[:, j]) & (m < sub_fin[:, j])
            b = np.flatnonzero(act)
            if b.size == 0:
                continue
            cid = C["suscripcion"]
            com = np.array([K.ID_COMERCIO[K.COMERCIOS_DE_CAT["suscripcion"][c]] for c in sub_com[b, j]], dtype=np.int16)
            es_dup = dup[b] & (j == 1)
            FM.add(b, d0 + sub_day[b, j] - 1, _secs(rng, b.size, 0, 6), sub_amt[b, j], sub_amt[b, j], False, cid, com, lab=np.where(es_dup, LAB_SUB_DUP, 0))
        # pagos pendientes de creditos informales
        for b_p, dia_p, monto_p in pend.pop(m, []):
            FM.add(b_p, d0 + min(dia_p, dm - 1), _secs(rng, 1, 9, 20), monto_p, monto_p, False, C["pago_credito_informal"], _com_aleatorio(rng, C["pago_credito_informal"], 1))

        # 7. gasto variable, con recorte si el saldo viene bajo
        gasto_mes = r_gasto * ing_obs * ipc
        estres = 0.55 + 0.45 * np.clip(saldo / np.maximum(0.5 * gasto_mes, 1.0), 0, 1)
        recorte_total = 0.55 + 0.45 * np.clip((saldo + 1.5 * base_nom) / np.maximum(1.5 * base_nom, 1.0), 0, 1)
        dd = np.arange(d0, d1 + 1)
        dom = ctx.dom[dd]
        pago = np.where((dom <= 4) | ((dom >= 15) & (dom <= 18)), 1.2, np.where(((dom >= 10) & (dom <= 14)) | (dom >= 26), 0.88, 1.0))
        rate = (tasa_bc[:, :, None] * dow_c[None, :, ctx.dow[dd]] * seas_c[None, :, mes - 1][:, :, None] * pago[None, None, :]
                * mult_tasa[:, :, d0:d1 + 1] * (np.where(DISCRECIONAL[None, :], estres[:, None], 1.0) * recorte_total[:, None])[:, :, None])
        n = rng.poisson(rate)
        idx = np.repeat(np.arange(n.size), n.ravel())
        bi, ci, di = np.unravel_index(idx, n.shape)
        monto = (monto_tipico[bi, ci] * ipc * mult_precio[bi, ci, d0 + di] * rng.lognormal(-sigma_c[ci] ** 2 / 2, sigma_c[ci]))
        es_at = (rng.random(bi.size) < p_atipico) & (ci != C["retiro_efectivo"])
        factor = rng.uniform(6, 20, bi.size)
        total_cli = np.bincount(bi, weights=monto, minlength=B)
        extra_cli = np.bincount(bi, weights=np.where(es_at, monto * (factor - 1), 0.0), minlength=B)
        resto_cli = np.maximum(total_cli - np.bincount(bi, weights=np.where(es_at, monto, 0.0), minlength=B), 1e-9)
        escala = np.clip(1 - extra_cli / resto_cli, 0.2, 1.0)
        monto = np.where(es_at, monto * factor, monto * escala[bi])
        k = rng.choice(3, bi.size, p=[.6, .3, .1])
        com = COM_TAB[ci, fav[bi, ci, k]]
        hora0 = np.where(ci == C["transporte"], 6, 8)
        secs = (hora0 * 3600 + rng.integers(0, 14 * 3600, bi.size)).astype(np.int32)
        FM.add(bi, d0 + di, secs, monto, monto, False, ci, com, lab=np.where(es_at, LAB_ATIPICO, 0))

        # 8. ahorro programado
        b = np.flatnonzero((s_ahorro > 0.01) & (saldo > base_nom * s_ahorro * 1.3))
        monto_a = base_nom[b] * s_ahorro[b]
        dia_a = min(ctx.pago_fin[m] + 1, d1)
        FM.add(b, dia_a, _secs(rng, b.size, 9, 12), monto_a, monto_a, False, C["ahorro_programado"], _com_aleatorio(rng, C["ahorro_programado"], b.size))
        # el excedente sobre dos meses de gasto se aparta: sin esto el saldo liquido crece sin limite
        barrido = np.where(saldo > 2.0 * gasto_mes, 0.7 * (saldo - 2.0 * gasto_mes), 0.0)
        b = np.flatnonzero(barrido > 50)
        FM.add(b, dia_a, _secs(rng, b.size, 12, 15), barrido[b], barrido[b], False, C["traspaso_ahorro"], _com_aleatorio(rng, C["traspaso_ahorro"], b.size))

        # 9. saldo corrido, rescates (ahorro o credito informal) y cierre del mes
        f = FM.concat()
        if len(f["b"]) == 0:
            continue
        signed = np.where(f["ing"], f["pen"], -f["pen"]).astype(np.float64)
        orden = np.lexsort((f["secs"], f["day"], f["b"]))
        f = {k_: v[orden] for k_, v in f.items()}
        signed = signed[orden]
        run = pd.Series(signed).groupby(f["b"]).cumsum().to_numpy() + saldo[f["b"]]
        inicios = np.flatnonzero(np.r_[True, f["b"][1:] != f["b"][:-1]])
        fines = np.r_[inicios[1:], len(f["b"])]
        minimos = np.minimum.reduceat(run, inicios)
        extras = []
        for gi in np.flatnonzero(minimos < 0):
            s_, e_ = inicios[gi], fines[gi]
            bi_ = f["b"][s_]
            rr = run[s_:e_]
            for _ in range(2):
                neg = np.flatnonzero(rr < 0)
                if neg.size == 0:
                    break
                kk = neg[0]
                deficit = -rr[kk] + 0.10 * base_nom[bi_]
                if bolsillo[bi_] > 1 and rng.random() < 0.85:
                    x = min(bolsillo[bi_], deficit)
                    bolsillo[bi_] -= x
                    cat_x = "retiro_ahorro"
                elif acceso[bi_] and rng.random() < 0.65:
                    x = deficit * 1.15
                    cat_x = "prestamo_informal"
                    if m + 1 < M:
                        pend.setdefault(m + 1, []).append((bi_, int(rng.integers(5, 26)), x * (1 + tasa_inf[bi_])))
                elif rr[kk] < -1.2 * base_nom[bi_]:
                    x = deficit * 0.9
                    cat_x = "transferencia_recibida"
                else:
                    break
                rr[kk:] += x
                extras.append((bi_, f["day"][s_ + kk], max(int(f["secs"][s_ + kk]) - 1, 0), x, C[cat_x]))
        if extras:
            eb, ed, es, ex, ec = (np.array(z) for z in zip(*extras))
            ec = ec.astype(np.int16)
            ecom = np.array([_com_aleatorio(rng, int(c_), 1)[0] for c_ in ec], dtype=np.int16)
            for k_, v in (("b", eb), ("day", ed), ("secs", es), ("monto", ex), ("pen", ex), ("ing", np.ones(len(eb), bool)),
                          ("cat", ec), ("com", ecom), ("moneda", np.zeros(len(eb), np.int8)), ("lab", np.zeros(len(eb), np.int8))):
                f[k_] = np.concatenate([f[k_], v.astype(f[k_].dtype)])
            orden = np.lexsort((f["secs"], f["day"], f["b"]))
            f = {k_: v[orden] for k_, v in f.items()}
        signed = np.where(f["ing"], f["pen"], -f["pen"]).astype(np.float64)
        f["saldo"] = (pd.Series(signed).groupby(f["b"]).cumsum().to_numpy() + saldo[f["b"]]).astype(np.float32)
        ahorros = (f["cat"] == C["ahorro_programado"]) | (f["cat"] == C["traspaso_ahorro"])
        np.add.at(bolsillo, f["b"][ahorros], f["pen"][ahorros])
        np.add.at(saldo, f["b"], signed)
        np.add.at(ing_dia, (f["b"][f["ing"]], f["day"][f["ing"]]), f["pen"][f["ing"]])
        np.add.at(gas_dia, (f["b"][~f["ing"]], f["day"][~f["ing"]]), f["pen"][~f["ing"]])
        for k_, v in f.items():
            F.d.setdefault(k_, []).append(v)

    filas = {k: (np.concatenate(v) if v else np.empty(0)) for k, v in F.d.items()}
    saldo_cierre = (saldo_ini[:, None] + np.cumsum(ing_dia.astype(np.float64) - gas_dia, axis=1)).astype(np.float32)
    return ResultadoLote(filas=filas, ing_dia=ing_dia, gas_dia=gas_dia, saldo_cierre=saldo_cierre, mult_ing=mult_ing)
