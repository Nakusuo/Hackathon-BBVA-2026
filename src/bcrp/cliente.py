"""Indicadores publicos del BCRP (sin clave). Cadena de respaldo: API en vivo -> cache en disco -> serie grabada en el repo."""
import json
import os
import time

import pandas as pd
import requests

from src.comun.rutas import DATA_RAW, ruta

MES_ES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6, "Jul": 7, "Ago": 8, "Set": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}
SERIES = {
    "tasa_referencia": ("PD04722MM", "tasa_referencia_bcrp", "mensual", "Tasa de referencia de la politica monetaria (%)"),
    "tipo_cambio_venta": ("PD04638PD", "tc_interbancario_venta_diario", "diaria", "Tipo de cambio interbancario venta (S/ por US$)"),
    "ipc_var_mensual": ("PN01271PM", "ipc_lima_var_mensual", "mensual", "IPC Lima Metropolitana, variacion % mensual"),
}
CACHE = ruta("data", "generado", "cache_bcrp")
TTL_SEGUNDOS = 6 * 3600


def _parsear(datos: dict) -> pd.Series:
    fechas, valores = [], []
    for p in datos["periods"]:
        partes = p["name"].split(".")
        try:
            f = pd.Timestamp(2000 + int(partes[2]), MES_ES[partes[1]], int(partes[0])) if len(partes) == 3 else pd.Timestamp(int(partes[1]), MES_ES[partes[0]], 1)
            v = float(p["values"][0])
        except (ValueError, KeyError, IndexError):
            continue
        fechas.append(f)
        valores.append(v)
    return pd.Series(valores, index=pd.DatetimeIndex(fechas)).sort_index()


def serie(nombre: str, desde: str = "2024-1", hasta: str = "2027-12", timeout: int = 15) -> tuple[pd.Series, str]:
    """Devuelve (serie, origen) con origen en {'api', 'cache', 'grabada'}."""
    codigo, archivo, frecuencia, _ = SERIES[nombre]
    per = f"{desde}-1/{hasta}-28" if frecuencia == "diaria" else f"{desde}/{hasta}"
    ruta_cache = os.path.join(CACHE, f"{archivo}.json")
    try:
        r = requests.get(f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{per}/esp", timeout=timeout, headers={"User-Agent": "analitica-hackathon/1.0"})
        r.raise_for_status()
        datos = r.json()
        s = _parsear(datos)
        if len(s):
            os.makedirs(CACHE, exist_ok=True)
            with open(ruta_cache, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False)
            return s, "api"
    except (requests.RequestException, ValueError, KeyError):
        pass
    if os.path.isfile(ruta_cache) and time.time() - os.path.getmtime(ruta_cache) < 7 * 24 * 3600:
        with open(ruta_cache, encoding="utf-8") as f:
            return _parsear(json.load(f)), "cache"
    with open(os.path.join(DATA_RAW, "bcrp", f"{archivo}.json"), encoding="utf-8") as f:
        return _parsear(json.load(f)), "grabada"


def ultimo_con_variacion(nombre: str) -> dict:
    """Ultimo valor, el anterior y la variacion. Sirve para detectar que la tasa bajo."""
    s, origen = serie(nombre)
    s = s.dropna()
    ult, prev = float(s.iloc[-1]), float(s.iloc[-2])
    return {"indicador": nombre, "descripcion": SERIES[nombre][3], "valor": ult, "fecha": str(s.index[-1].date()), "valor_previo": prev, "fecha_previa": str(s.index[-2].date()),
            "variacion": round(ult - prev, 4), "origen": origen}
