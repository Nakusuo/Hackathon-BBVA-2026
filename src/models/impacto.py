"""Impacto en soles de seguir a Lucas: reproduccion contrafactual sobre los flujos reales del periodo de prueba.
Supuesto central: los flujos no reaccionan al cambio (se aplica la politica sobre lo que de verdad ocurrio) y cada accion se adopta
con la probabilidad de aceptacion del cliente. Todo supuesto queda en SUPUESTOS y se muestra junto al resultado."""
import numpy as np
import pandas as pd

from src.models.datos import Series

SUPUESTOS = {
    "tasa_mensual_por_cubrir_el_hueco": 0.10,   # costo de cubrir un dia en rojo con credito informal (supuesto del equipo)
    "fraccion_apartada_10_fijo": 0.10,          # baseline del plan
    "recorte_hormiga": 0.20,                    # efecto de la recomendacion de gasto hormiga
    "recorte_hormiga_en_alerta": 0.50,           # recorte adicional del gasto hormiga durante una alerta de riesgo de rojo (14 dias)
    "dias_de_alerta": 14,
    "umbral_alerta_p_rojo": 0.25,
    "asignacion_sueldo_lucas": 0.95,            # parte del ingreso medio de 90 dias que Lucas libera por dia
    "umbral_irregular_cv": 0.40,                # desde aqui se recomienda Sueldo Lucas
}


def flujos_especiales(tx: pd.DataFrame, s: Series) -> tuple[np.ndarray, np.ndarray]:
    """Gasto hormiga y cobros de suscripciones duplicadas por cliente y dia, sobre movimientos sin duplicados de ingesta."""
    t = tx[~tx["transaction_id"].astype(str).str.endswith("D")].drop_duplicates("transaction_id")
    pos_c = pd.Series(np.arange(len(s.ids)), index=s.ids)
    c = t["customer_id"].astype(str).map(pos_c).to_numpy()
    d = s.fechas.searchsorted(t["fecha_hora"].dt.normalize())
    horm = t["categoria"].astype(str).isin(["delivery", "snacks"]).to_numpy()
    dup = t["es_suscripcion_duplicada"].to_numpy()
    m = t["monto_pen"].to_numpy(dtype=float)
    B, D = len(s.ids), len(s.fechas)
    hormiga = np.zeros((B, D))
    sdup = np.zeros((B, D))
    np.add.at(hormiga, (c[horm], d[horm]), m[horm])
    np.add.at(sdup, (c[dup], d[dup]), m[dup])
    return hormiga, sdup


def _correr(s: Series, d0: int, d1: int, politica: str, acepta: np.ndarray, hormiga, sdup, irregular: np.ndarray, sup: dict, alertas: np.ndarray | None = None) -> dict:
    B = len(s.ids)
    ing, gas = s.ing.astype(float), s.gas.astype(float)
    cs = np.concatenate([np.zeros((B, 1)), np.cumsum(ing, 1)], 1)
    saldo = s.saldo[:, d0 - 1].astype(float).copy()
    reserva = np.zeros(B)
    dias_rojo = np.zeros(B)
    costo = np.zeros(B)
    if politica == "lucas":
        gas = gas - acepta[:, 0:1] * sdup - acepta[:, 1:2] * sup["recorte_hormiga"] * hormiga
        if alertas is not None:  # aviso anticipado del pronostico: durante la alerta se recorta el gasto hormiga restante
            gas = gas - acepta[:, 3:4] * alertas * sup["recorte_hormiga_en_alerta"] * hormiga
    sueldo = (politica == "lucas") & irregular
    for d in range(d0, d1 + 1):
        entra = ing[:, d]
        gasto_dia = gas[:, d]
        if politica in ("diez_fijo", "diez_fijo_ajustado"):
            reserva += sup["fraccion_apartada_10_fijo"] * entra
            if politica == "diez_fijo_ajustado":  # aparta el 10 % y recorta del gasto ese mismo monto: la caja diaria no cambia
                gasto_dia = gasto_dia - sup["fraccion_apartada_10_fijo"] * entra
            entra = (1 - sup["fraccion_apartada_10_fijo"]) * entra
        elif politica == "lucas":
            activo = sueldo & (acepta[:, 2] == 1)
            reserva += np.where(activo, entra, 0.0)
            media90 = (cs[:, d] - cs[:, max(d - 90, 0)]) / 90
            libera = np.where(activo, np.minimum(reserva, sup["asignacion_sueldo_lucas"] * media90), 0.0)
            reserva -= libera
            entra = np.where(activo, libera, entra)
        saldo = saldo + entra - gasto_dia
        if politica == "lucas":  # el apartado de Sueldo Lucas se puede usar para cubrir un hueco; el 10 % fijo del baseline queda bloqueado
            cubre = np.minimum(reserva, np.maximum(-saldo, 0.0))
            saldo += cubre
            reserva -= cubre
        dias_rojo += saldo < 0
        costo += np.maximum(-saldo, 0.0) * sup["tasa_mensual_por_cubrir_el_hueco"] / 30
    return {"dias_rojo": dias_rojo, "colchon": np.maximum(saldo, 0.0) + reserva, "costo_hueco": costo}


def simular(s: Series, clientes: pd.DataFrame, features: pd.DataFrame, tx: pd.DataFrame, desde: str, hasta: str, semilla: int = 0, repeticiones: int = 5,
            sup: dict | None = None, origenes_alerta: pd.DataFrame | None = None) -> dict:
    sup = {**SUPUESTOS, **(sup or {})}
    d0 = int(s.fechas.searchsorted(pd.Timestamp(desde)))
    d1 = int(s.fechas.searchsorted(pd.Timestamp(hasta), side="right")) - 1
    hormiga, sdup = flujos_especiales(tx, s)
    cl = clientes.reindex(s.ids)
    irregular = (features["cv_ingreso"].reindex(s.ids).to_numpy() > sup["umbral_irregular_cv"])
    p_acepta = cl["prob_acepta_reco"].to_numpy()
    peso = cl["peso_muestral"].to_numpy()
    meses = (d1 - d0 + 1) / 30.4
    ingreso_mensual = features["ingreso_medio"].reindex(s.ids).to_numpy()
    alertas = None
    if origenes_alerta is not None:  # origenes con p_rojo predicho: [cliente_idx, dia_idx, p_rojo]
        alertas = np.zeros((len(s.ids), len(s.fechas)))
        a = origenes_alerta[origenes_alerta["p_rojo"] >= sup["umbral_alerta_p_rojo"]]
        for c, t in zip(a["cliente_idx"].to_numpy(), a["dia_idx"].to_numpy()):
            alertas[c, t + 1:t + 1 + sup["dias_de_alerta"]] = 1.0
    rng = np.random.default_rng(semilla)
    res = {}
    for pol in ("nada", "diez_fijo", "diez_fijo_ajustado", "lucas"):
        reps = []
        for r in range(repeticiones if pol == "lucas" else 1):
            acepta = (rng.random((len(s.ids), 4)) < p_acepta[:, None]).astype(int)
            reps.append(_correr(s, d0, d1, pol, acepta, hormiga, sdup, irregular, sup, alertas))
        res[pol] = {k: np.mean([x[k] for x in reps], axis=0) for k in reps[0]}
    def pm(x, mask=None):
        m = np.ones(len(x), bool) if mask is None else mask
        return float(np.average(x[m], weights=peso[m]))
    tabla = {}
    for pol, r in res.items():
        tabla[pol] = {"dias_en_rojo_por_cliente_mes": pm(r["dias_rojo"] / meses), "colchon_final_soles": pm(r["colchon"]), "colchon_final_meses_de_ingreso": pm(r["colchon"] / ingreso_mensual),
                      "costo_de_cubrir_el_hueco_soles_por_mes": pm(r["costo_hueco"] / meses)}
    rng2 = np.random.default_rng(semilla + 1)
    n = len(s.ids)
    dif = {}
    for pol in ("diez_fijo", "diez_fijo_ajustado", "lucas"):
        for ref in ("nada", "diez_fijo_ajustado"):
            if pol == ref:
                continue
            vals = {"dias_rojo_evitados_por_cliente_mes": (res[ref]["dias_rojo"] - res[pol]["dias_rojo"]) / meses, "colchon_adicional_soles": res[pol]["colchon"] - res[ref]["colchon"],
                    "intereses_evitados_soles_por_mes": (res[ref]["costo_hueco"] - res[pol]["costo_hueco"]) / meses}
            out = {}
            for k, v in vals.items():
                boots = [np.average(v[i], weights=peso[i]) for i in (rng2.integers(0, n, n) for _ in range(300))]
                out[k] = {"media": pm(v), "ic95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
            dif[f"{pol}_vs_{ref}"] = out
    seg = clientes.reindex(s.ids)["segmento"].to_numpy()
    por_segmento = pd.DataFrame({sg: {"dias_rojo_nada": pm(res["nada"]["dias_rojo"] / meses, seg == sg), "dias_rojo_lucas": pm(res["lucas"]["dias_rojo"] / meses, seg == sg),
                                      "colchon_nada": pm(res["nada"]["colchon"], seg == sg), "colchon_lucas": pm(res["lucas"]["colchon"], seg == sg)} for sg in np.unique(seg)}).T
    return {"tabla": pd.DataFrame(tabla).T, "diferencias": dif, "por_segmento": por_segmento, "supuestos": sup, "ventana": (desde, hasta), "meses": meses}
