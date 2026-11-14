"""Reloj unico del agente. Todo lo que depende de la fecha (calendario laboral, vigencia de normas y de alertas) pregunta aqui y no a date.today().
Se puede fijar para pruebas y demostraciones con fijar() o con la variable de entorno LUCAS_HOY (AAAA-MM-DD). Una fecha invalida se ignora y rige la real."""
import os
from datetime import date

_FIJO: date | None = None


def fijar(d: date | str | None) -> None:
    """Fija el 'hoy' del agente (None vuelve a la fecha real)."""
    global _FIJO
    _FIJO = date.fromisoformat(d) if isinstance(d, str) else d


def hoy() -> date:
    if _FIJO is not None:
        return _FIJO
    valor = os.environ.get("LUCAS_HOY", "").strip()
    if valor:
        try:
            return date.fromisoformat(valor)
        except ValueError:
            pass
    return date.today()
