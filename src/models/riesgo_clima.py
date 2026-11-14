"""Exposicion de un departamento a lluvias por encima de lo normal (El Nino costero), con la fuente oficial que la sustenta."""
import pandas as pd

from src.generador.contexto import cargar_yaml

_CFG = None


def _cfg() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = cargar_yaml("zonas_riesgo_fen.yaml")
    return _CFG


def exposicion_fen(departamento: str) -> dict:
    c = _cfg()
    for nivel in ("alta", "media", "posible"):
        n = c["niveles"][nivel]
        if departamento in n["departamentos"]:
            return {"nivel": nivel, "departamento": departamento, "estado_dato": n["estado"], "motivo": n["motivo"]}
    return {"nivel": "baja", "departamento": departamento, "estado_dato": "parcial", "motivo": c["niveles"]["baja"]["motivo"]}


def alerta_fen(departamento: str, hoy: str | None = None) -> dict | None:
    """Alerta solo si hay exposicion y el aviso del ENFEN sigue vigente. Devuelve las acciones de prevencion y la fuente."""
    c = _cfg()
    e = exposicion_fen(departamento)
    fecha = pd.Timestamp(hoy) if hoy else pd.Timestamp.today().normalize()
    if e["nivel"] == "baja" or fecha > pd.Timestamp(c["vigente_hasta"]):
        return None
    return {**e, "vigente_hasta": c["vigente_hasta"], "acciones": c["acciones_prevencion"], "fuente": c["fuente"]["comunicado_20"],
            "documento": "docs/fuentes/enfen/enfen_comunicado_20_2026.txt"}
