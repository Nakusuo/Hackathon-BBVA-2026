"""Memoria del usuario en archivos JSON locales: metas, preferencias, respuesta a cada recomendacion y puntos. Se puede ver y olvidar."""
import json
import os
from datetime import datetime, timedelta

from src.comun.rutas import ruta

CARPETA = ruta("data", "generado", "memoria")


def _archivo(cid: str) -> str:
    return os.path.join(CARPETA, f"{cid}.json")


def cargar(cid: str) -> dict:
    if os.path.isfile(_archivo(cid)):
        with open(_archivo(cid), encoding="utf-8") as f:
            return json.load(f)
    return {"customer_id": cid, "metas": [], "preferencias": {}, "respuestas_reco": {}, "puntos": 0, "movimientos_puntos": [], "avisos": []}


def guardar(m: dict) -> None:
    os.makedirs(CARPETA, exist_ok=True)
    with open(_archivo(m["customer_id"]), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def registrar_respuesta(cid: str, reco_id: str, respuesta: str) -> dict:
    """respuesta: 'util' o 'no_me_sirve'. Las recomendaciones rechazadas bajan en el ranking."""
    m = cargar(cid)
    m["respuestas_reco"][reco_id] = respuesta
    guardar(m)
    return m


def sumar_puntos(cid: str, accion: str, puntos: int) -> dict:
    m = cargar(cid)
    m["puntos"] += int(puntos)
    m["movimientos_puntos"].append({"fecha": datetime.now().isoformat(timespec="seconds"), "accion": accion, "puntos": int(puntos)})
    guardar(m)
    return m


def puede_avisar(cid: str, ahora: datetime | None = None, maximo_semana: int = 3) -> bool:
    ahora = ahora or datetime.now()
    m = cargar(cid)
    ultimos = [a for a in m["avisos"] if datetime.fromisoformat(a["fecha"]) > ahora - timedelta(days=7)]
    return len(ultimos) < maximo_semana


def registrar_aviso(cid: str, tipo: str, ahora: datetime | None = None) -> None:
    m = cargar(cid)
    m["avisos"].append({"fecha": (ahora or datetime.now()).isoformat(timespec="seconds"), "tipo": tipo})
    guardar(m)


def olvidar(cid: str) -> bool:
    """Borra todo lo que Lucas sabe del usuario (derecho de supresion)."""
    if os.path.isfile(_archivo(cid)):
        os.remove(_archivo(cid))
        return True
    return False
