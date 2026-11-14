"""Nombres de nivel por segmento y programa de puntos que premia conductas financieras sanas."""
import numpy as np
import pandas as pd

from src.generador.contexto import cargar_yaml
from src.models.salud import puntaje_salud

CFG = None


def _cfg() -> dict:
    global CFG
    if CFG is None:
        CFG = cargar_yaml("niveles.yaml")
    return CFG


def nombres_por_segmento(f: pd.DataFrame, etiquetas: np.ndarray) -> dict:
    """Ordena los segmentos por la salud mediana de sus clientes y les asigna la escalera de nombres de menor a mayor."""
    c = _cfg()
    salud = puntaje_salud(f).groupby(etiquetas).median().sort_values()
    escalera = c["escalera"]
    k = len(salud)
    pos = np.unique(np.round(np.linspace(0, len(escalera) - 1, k)).astype(int))
    if len(pos) < k:
        pos = np.arange(k)
    return {int(seg): escalera[p] for seg, p in zip(salud.index, pos)}


def ficha(nivel: str) -> dict:
    return {"id": nivel, **_cfg()["niveles"][nivel]}


def siguiente(nivel: str) -> str | None:
    esc = _cfg()["escalera"]
    i = esc.index(nivel)
    return esc[i + 1] if i + 1 < len(esc) else None


def progreso(nivel: str, f: pd.Series, salud: float) -> dict:
    """Que le falta al cliente para subir al nivel siguiente, con los umbrales de la configuracion."""
    sig = siguiente(nivel)
    if sig is None:
        return {"siguiente": None, "faltantes": [], "cumple": True}
    req = _cfg()["niveles"][nivel].get("para_subir", {})
    falta = []
    if "salud_minima" in req and salud < req["salud_minima"]:
        falta.append({"que": "salud financiera", "tienes": round(float(salud), 1), "necesitas": req["salud_minima"]})
    if "dias_rojo_3m_max" in req and f["dias_rojo_3m"] > req["dias_rojo_3m_max"]:
        falta.append({"que": "dias en rojo en 3 meses", "tienes": int(f["dias_rojo_3m"]), "necesitas": f"{req['dias_rojo_3m_max']} o menos"})
    if "colchon_meses_min" in req and f["colchon_observado"] < req["colchon_meses_min"]:
        falta.append({"que": "colchon en meses de ingreso", "tienes": round(float(f["colchon_observado"]), 2), "necesitas": req["colchon_meses_min"]})
    if "ahorro_pct_min" in req and f["ahorro_pct"] < req["ahorro_pct_min"]:
        falta.append({"que": "ahorro como parte del ingreso", "tienes": round(float(f["ahorro_pct"]), 3), "necesitas": req["ahorro_pct_min"]})
    return {"siguiente": sig, "faltantes": falta, "cumple": not falta}


def puntos_por(accion: str, nivel: str, veces: int = 1) -> dict:
    """Puntos de una conducta sana, con el multiplicador del nivel. El valor en soles es un supuesto visible."""
    c = _cfg()
    base = c["puntos"]["acciones"][accion]
    mult = c["niveles"][nivel]["multiplicador_puntos"]
    pts = int(round(base * mult)) * veces
    return {"accion": accion, "puntos_base": base, "multiplicador": mult, "puntos": pts, "equivale_a_soles": round(pts * c["puntos"]["valor_por_punto_soles"], 2),
            "supuesto": "el valor por punto es un supuesto del equipo"}


def canjes_disponibles(puntos: int) -> list[dict]:
    return [x for x in _cfg()["canje"] if x["puntos"] <= puntos]


def nivel_individual(nivel_segmento: str, salud: float) -> str:
    """El nivel del cliente es el menor entre el de su segmento y el que permite su salud financiera actual.
    Asi un cliente de un segmento alto con una salud baja no recibe un nombre que no le corresponde."""
    esc = _cfg()["escalera"]
    requisito = {esc[i + 1]: _cfg()["niveles"][esc[i]].get("para_subir", {}).get("salud_minima", 0) for i in range(len(esc) - 1)}
    por_salud = 0
    for i, nombre in enumerate(esc):
        if i == 0 or salud >= requisito.get(nombre, 0):
            por_salud = i
        else:
            break
    return esc[min(esc.index(nivel_segmento), por_salud)]
