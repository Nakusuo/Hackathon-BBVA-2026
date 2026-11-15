"""RAG: funciones puras de la consulta (siglas y preguntas compuestas). No necesitan Ollama ni el indice."""
import pytest

from src.rag.indice import descomponer, expandir_siglas


def test_la_sigla_se_expande_una_sola_vez_y_conserva_el_texto_original():
    assert expandir_siglas("¿Qué es la TCEA y cómo baja la TCEA?") == "¿Qué es la TCEA (tasa de costo efectivo anual) y cómo baja la TCEA?"


@pytest.mark.parametrize("texto", ["¿Que es la tasa de costo efectivo anual?", "estea y ctsx no son siglas", "Quiero ahorrar para mi viaje"])
def test_no_toca_lo_que_no_es_una_sigla_completa(texto):
    assert expandir_siglas(texto) == texto


def test_la_sigla_se_reconoce_en_minusculas_y_varias_a_la_vez():
    e = expandir_siglas("cuando me cae la cts si estoy en eps")
    assert "cts (compensacion por tiempo de servicios)" in e and "eps (entidad prestadora de salud)" in e


def test_una_pregunta_compuesta_se_parte_en_sus_dos_preguntas_y_la_original_va_primero():
    q = "¿Qué es la TCEA y qué derechos tengo si me atraso en un pago?"
    assert descomponer(q) == [q, "Qué es la TCEA", "qué derechos tengo si me atraso en un pago"]


@pytest.mark.parametrize("q", ["¿Cómo armo un presupuesto mensual?", "¿Qué hago si me atrasé en el pago de mis cuentas?", "Ahorro y gasto lo justo", "¿Hasta cuándo?"])
def test_una_pregunta_simple_no_se_parte(q):
    assert descomponer(q) == [q]
