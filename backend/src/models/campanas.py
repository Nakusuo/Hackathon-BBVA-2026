"""Convenios del banco con comercios aliados (catalogo de ejemplo, con aliados inventados). Es el mismo archivo que lee el front,
para que el chat y las pantallas ofrezcan lo mismo. Aqui solo se elige el convenio que toca el tema de la pregunta y se calcula su descuento."""
import json
import re
import unicodedata
from datetime import date
from functools import lru_cache

from src.comun.rutas import ruta

# Destinos fuera del Peru: un convenio de pasajes nacionales no los cubre y se dice, en vez de ofrecerlo como si aplicara
EXTRANJERO = (r"brasil|argentina|chile|colombia|ecuador|bolivia|mexico|cancun|estados unidos|eeuu|miami|orlando|europa|espana|italia|francia|japon|"
              r"extranjero|exterior|internacional|fuera del pais")


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


@lru_cache(maxsize=1)
def catalogo() -> list[dict]:
    with open(ruta("data", "catalogo_campanas.json"), encoding="utf-8") as f:
        return json.load(f)["campanas"]


def campana_para(pregunta: str, hoy: date) -> dict | None:
    """El convenio vigente cuyo tema nombra la pregunta, con `aplica` y su motivo cuando no cubre lo que se pide."""
    texto = _sin_tildes(pregunta)
    for c in catalogo():
        if date.fromisoformat(c["hasta"]) < hoy or not any(re.search(rf"\b{t}s?\b", texto) for t in c["temas"]):
            continue
        fuera = c.get("solo_nacional") and re.search(EXTRANJERO, texto)
        return {**c, "aplica": not fuera, "motivo": f"cubre solo {c['rubro']}" if fuera else None}
    return None


def descuento(c: dict, precio: float) -> float:
    if not precio or not c.get("aplica", True):
        return 0.0
    if c.get("fijo"):
        return float(min(c["fijo"], precio))
    return float(min(round(precio * c["porcentaje"] / 100), c["tope"]))


def beneficio(c: dict) -> str:
    return f"S/ {c['fijo']:,.0f} de descuento" if c.get("fijo") else f"{c['porcentaje']} % de descuento (hasta S/ {c['tope']:,.0f})"
