"""Respuestas de `demo-001`: las genera el motor del front (frontend/scripts/exportar-persona-demo.mjs) y la API
solo las sirve, para que lo que devuelve coincida con lo que muestra la pantalla. No hay cifras escritas aquí."""
import json
from functools import cache

from src.comun.rutas import DATA_SAMPLE, ruta

ID_DEMO = "demo-001"


@cache
def _leer(nombre: str) -> dict:
    with open(ruta(DATA_SAMPLE, "demo-001", nombre), encoding="utf-8") as archivo:
        return json.load(archivo)


def respuesta(nombre: str) -> dict:
    """Copia de la respuesta guardada: quien la recibe puede modificarla sin tocar la que se comparte."""
    return json.loads(json.dumps(_leer(nombre)))


def pronostico(dias: int) -> dict:
    datos = respuesta("forecast.json")
    datos["forecast"] = datos["forecast"][:dias]
    datos["horizon_days"] = len(datos["forecast"])
    return datos
