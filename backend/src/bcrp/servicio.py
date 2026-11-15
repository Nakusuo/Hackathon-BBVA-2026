"""Tipo de cambio e inflación del BCRP: API → caché → último valor → serie grabada.

Solo da contexto (por ejemplo, para un pago propio en US$). Nunca se usa para sugerir
comprar o vender dólares, ni para predecir el tipo de cambio.
"""

import json
import logging
import time
from datetime import date
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

URL_API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
RAIZ = Path(__file__).resolve().parents[3]
RUTA_CACHE = RAIZ / "data" / "bcrp" / "cache.json"
RUTA_GRABADA = RAIZ / "data" / "bcrp" / "serie_grabada.json"
CACHE_TTL_S = 6 * 3600
TIMEOUT_S = 5

SERIES = {
    "tipo_cambio": {
        "codigo": "PD04638PD",
        "nombre": "TC interbancario venta (S/ por US$)",
        "frecuencia": "diaria",
    },
    "inflacion_12m": {
        "codigo": "PN01273PM",
        "nombre": "Inflación Lima Metropolitana, var. % 12 meses",
        "frecuencia": "mensual",
    },
}

_MESES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}  # fmt: skip


class SerieNoDisponible(Exception):
    """No hay valor ni en la API, ni en caché, ni en la serie grabada."""


def periodo_iso(nombre: str) -> str:
    """«12.Nov.26» → «2026-11-12»; «Oct.2026» → «2026-10»."""
    partes = nombre.split(".")
    if len(partes) == 3:
        dia, mes, anio = partes
        return date(2000 + int(anio), _MESES[mes.lower()], int(dia)).isoformat()
    mes, anio = partes
    return f"{int(anio):04d}-{_MESES[mes.lower()]:02d}"


def ultimo_valor(respuesta_api: dict) -> tuple[str, float]:
    """Último periodo con dato; el BCRP marca «n.d.» los días sin publicación."""
    for p in reversed(respuesta_api.get("periods", [])):
        valor = p["values"][0]
        if valor != "n.d.":
            return periodo_iso(p["name"]), float(valor)
    raise SerieNoDisponible("la API no trajo ningún valor")


def rango(frecuencia: str, hoy: date) -> tuple[str, str]:
    if frecuencia == "diaria":
        inicio = date.fromordinal(hoy.toordinal() - 30)
        return inicio.isoformat(), hoy.isoformat()
    anio, mes = (hoy.year, hoy.month - 6) if hoy.month > 6 else (hoy.year - 1, hoy.month + 6)
    return f"{anio}-{mes}", f"{hoy.year}-{hoy.month}"


def _leer(ruta: Path) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


class ServicioBCRP:
    def __init__(
        self,
        cliente: httpx.Client | None = None,
        ruta_cache: Path = RUTA_CACHE,
        ruta_grabada: Path = RUTA_GRABADA,
        reloj=time.time,
    ):
        self.cliente = cliente or httpx.Client(timeout=TIMEOUT_S)
        self.ruta_cache = ruta_cache
        self.ruta_grabada = ruta_grabada
        self.reloj = reloj

    def consultar_api(self, serie: str, hoy: date | None = None) -> tuple[str, float]:
        info = SERIES[serie]
        inicio, fin = rango(info["frecuencia"], hoy or date.today())
        r = self.cliente.get(f"{URL_API}/{info['codigo']}/json/{inicio}/{fin}/esp")
        r.raise_for_status()
        return ultimo_valor(r.json())

    def obtener(self, serie: str) -> dict:
        """Devuelve {serie, nombre, codigo, periodo, valor, origen}; `origen` dice de dónde salió."""
        info = SERIES[serie]
        cache = _leer(self.ruta_cache)
        guardado = cache.get(serie)
        if guardado and self.reloj() - guardado["consultado_en"] < CACHE_TTL_S:
            return self._resultado(serie, guardado, "cache")
        try:
            periodo, valor = self.consultar_api(serie)
        except (httpx.HTTPError, ValueError, KeyError, SerieNoDisponible) as e:
            log.warning("BCRP sin respuesta para %s (%s)", info["codigo"], type(e).__name__)
            if guardado:
                return self._resultado(serie, guardado, "ultimo_valor")
            grabada = _leer(self.ruta_grabada).get(serie)
            if not grabada:
                raise SerieNoDisponible(serie) from e
            return self._resultado(serie, grabada, "serie_grabada")
        nuevo = {"periodo": periodo, "valor": valor, "consultado_en": self.reloj()}
        cache[serie] = nuevo
        self.ruta_cache.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_cache.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        return self._resultado(serie, nuevo, "api")

    def _resultado(self, serie: str, dato: dict, origen: str) -> dict:
        info = SERIES[serie]
        return {
            "serie": serie,
            "nombre": info["nombre"],
            "codigo": info["codigo"],
            "periodo": dato["periodo"],
            "valor": round(dato["valor"], 3),
            "origen": origen,
        }


def fx_contrato(resultado: dict) -> dict:
    """Pasa `obtener("tipo_cambio")` a la respuesta de `GET /api/v1/fx` (contrato MG-01)."""
    respaldo = resultado["origen"] in ("ultimo_valor", "serie_grabada")
    return {
        "base": "USD",
        "quote": "PEN",
        "rate": resultado["valor"],
        "date": resultado["periodo"],
        "source": f"BCRP {resultado['codigo']}",
        "is_fallback": respaldo,
        "is_stale": respaldo,
    }


def grabar_respaldo() -> None:
    """Graba los últimos valores en `serie_grabada.json` para la demo sin red."""
    servicio = ServicioBCRP()
    grabada = {}
    for serie in SERIES:
        periodo, valor = servicio.consultar_api(serie)
        grabada[serie] = {"periodo": periodo, "valor": valor, "grabado": date.today().isoformat()}
    RUTA_GRABADA.parent.mkdir(parents=True, exist_ok=True)
    RUTA_GRABADA.write_text(json.dumps(grabada, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    grabar_respaldo()
