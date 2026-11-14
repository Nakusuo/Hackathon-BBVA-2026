"""Programa de puntos sostenible: puntos por consumo (solo con idoneidad), por ahorro y por conductas sanas, con tope de reinversion.
La economia se mide sobre los movimientos reales del ultimo anio con supuestos visibles. Dos lecturas: bruta (la comision del consumo financia los puntos)
e incremental (que parte del consumo debe ser nueva para que el programa se pague solo)."""
import numpy as np
import pandas as pd

from src.generador.contexto import cargar_yaml
from src.models import niveles as N

_CFG = None


def cfg() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = cargar_yaml("niveles.yaml")
    return _CFG


def idoneo_para_puntos_de_consumo(nivel: str, dias_rojo_3m: float) -> bool:
    """El consumo solo da puntos a quien no tiene la caja en tension: no se incentiva gastar a quien no puede."""
    c = cfg()["programa"]["idoneidad_de_consumo"]
    esc = cfg()["escalera"]
    return dias_rojo_3m <= c["dias_rojo_3m_max"] and esc.index(nivel) >= esc.index(c["nivel_minimo"])


def puntos_mes(nivel: str, consumo_elegible: float, ahorro_apartado: float, dias_rojo_3m: float, quincenas_sin_rojo: float, meses_con_aporte: float = 0.0) -> dict:
    """Puntos del mes de un cliente. Devuelve el detalle para poder explicarlo al usuario."""
    c = cfg()
    pr = c["programa"]
    mult = c["niveles"][nivel]["multiplicador_puntos"]
    por_consumo = pr["puntos_por_cada_10_soles_de_consumo"][nivel] * consumo_elegible / 10 if idoneo_para_puntos_de_consumo(nivel, dias_rojo_3m) else 0.0
    por_ahorro = pr["puntos_por_cada_100_soles_apartados"][nivel] * ahorro_apartado / 100
    por_acciones = (c["puntos"]["acciones"]["quincena_sin_dias_en_rojo"] * quincenas_sin_rojo + c["puntos"]["acciones"]["aporte_a_meta_de_ahorro"] * meses_con_aporte) * mult
    total = min(por_consumo + por_ahorro + por_acciones, c["puntos"]["tope_mensual"])
    return {"consumo": por_consumo, "ahorro": por_ahorro, "acciones": por_acciones, "total": total}


def economia(df: pd.DataFrame, peso: pd.Series | None = None, usuarios: int = 100_000) -> dict:
    """df: una fila por cliente con nivel, consumo_elegible, ahorro_apartado, dias_rojo_3m, quincenas_sin_rojo, meses_con_aporte (valores mensuales promedio)."""
    c = cfg()
    se = c["programa"]["supuestos_economicos"]
    vp = c["puntos"]["valor_por_punto_soles"]
    canje = se["porcentaje_de_puntos_que_se_canjea"]
    filas = []
    for _, r in df.iterrows():
        p = puntos_mes(r["nivel"], r["consumo_elegible"], r["ahorro_apartado"], r["dias_rojo_3m"], r["quincenas_sin_rojo"], r["meses_con_aporte"])
        filas.append({**p, "consumo": p["consumo"], "elegible": r["consumo_elegible"], "nivel": r["nivel"]})
    x = pd.DataFrame(filas, index=df.index)
    x["costo_anual"] = x["total"] * 12 * vp * canje
    x["comision_anual"] = x["elegible"] * 12 * se["comision_por_consumo"]
    x["margen_ahorro_anual"] = df["ahorro_apartado"] * 6 * se["margen_anual_sobre_saldo_apartado"]   # saldo medio apartado en el anio = 6 meses de aporte
    x["ingreso_anual"] = x["comision_anual"] + x["margen_ahorro_anual"]
    w = peso if peso is not None else pd.Series(1.0, index=df.index)
    sal = {}
    for niv, g in x.groupby("nivel"):
        ww = w.loc[g.index]
        wm = lambda col: float(np.average(g[col], weights=ww))  # noqa: E731
        costo, comision, cons, ingreso = wm("costo_anual"), wm("comision_anual"), wm("elegible") * 12, wm("ingreso_anual")
        sal[niv] = {"clientes": int(len(g)), "consumo_elegible_anual": cons, "puntos_por_mes": wm("total"), "costo_de_puntos_anual": costo, "comision_por_consumo_anual": comision,
                    "margen_por_ahorro_anual": wm("margen_ahorro_anual"), "ingreso_anual": ingreso, "costo_sobre_ingreso": costo / ingreso if ingreso else None,
                    "consumo_por_cada_sol_de_puntos": (cons / (costo / canje)) if costo else None, "neto_bruto_anual": ingreso - costo,
                    "mejora_de_ingreso_necesaria_para_pagarse": (costo / ingreso) if ingreso else None}
    pw = w / w.sum()
    tot = {k: float((x[k] * pw).sum()) for k in ("costo_anual", "comision_anual", "margen_ahorro_anual", "ingreso_anual", "total")}
    tot["costo_sobre_ingreso"] = tot["costo_anual"] / tot["ingreso_anual"] if tot["ingreso_anual"] else None
    tot["neto_bruto_por_usuario_anual"] = tot["ingreso_anual"] - tot["costo_anual"]
    tot["neto_bruto_anual_escenario"] = tot["neto_bruto_por_usuario_anual"] * usuarios
    tot["usuarios"] = usuarios
    tot["puntos_por_usuario_al_mes"] = tot.pop("total")
    return {"por_nivel": sal, "total": tot, "supuestos": se, "valor_por_punto": vp}


def verificar_topes() -> dict:
    """Comprueba que cada tasa de puntos por consumo respeta el tope de reinversion de la comision. Devuelve el costo sobre la comision por nivel."""
    pr = cfg()["programa"]
    vp = cfg()["puntos"]["valor_por_punto_soles"]
    se = pr["supuestos_economicos"]
    return {n: (r * vp / 10) / se["comision_por_consumo"] for n, r in pr["puntos_por_cada_10_soles_de_consumo"].items()}


def beneficios(nivel: str) -> list:
    return cfg()["programa"]["beneficios_por_nivel"][nivel]


def resumen_para_usuario(nivel: str) -> dict:
    """Lo que el usuario ve: cuanto gana por consumo y por ahorro en su nivel y que beneficios tiene. Sin cifras de la entidad."""
    pr = cfg()["programa"]
    ficha = N.ficha(nivel)
    return {"nivel": ficha["titulo"], "puntos_por_cada_10_soles_de_consumo": pr["puntos_por_cada_10_soles_de_consumo"][nivel], "puntos_por_cada_100_soles_apartados": pr["puntos_por_cada_100_soles_apartados"][nivel],
            "beneficios": beneficios(nivel), "el_consumo_suma_puntos": pr["puntos_por_cada_10_soles_de_consumo"][nivel] > 0,
            "nota": "Los puntos por consumo se activan cuando tu caja esta ordenada; ahorrar siempre suma." if pr["puntos_por_cada_10_soles_de_consumo"][nivel] == 0 else ""}
