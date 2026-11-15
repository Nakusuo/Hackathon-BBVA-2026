"""Formato de cifras para textos al usuario."""

from datetime import date

_MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def soles(monto: float) -> str:
    """«S/ 1 680» o «S/ 85.50»: espacio de miles para no confundir con el decimal."""
    entero = round(monto) == round(monto, 2)
    texto = f"{abs(monto):,.0f}" if entero else f"{abs(monto):,.2f}"
    signo = "-" if monto < 0 else ""
    return f"{signo}S/ {texto.replace(',', ' ')}"


def fecha_larga(iso: str) -> str:
    """«jueves 27 de noviembre»."""
    d = date.fromisoformat(iso[:10])
    return f"{_DIAS[d.weekday()]} {d.day} de {_MESES[d.month - 1]}"
