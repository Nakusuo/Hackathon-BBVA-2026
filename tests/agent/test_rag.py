"""JF-05: RAG por módulos sobre el índice de Diego, sin Ollama (embedding falso)."""

import numpy as np
import pytest

from agent.chat import responder
from agent.grafo import construir
from agent.juez import juzgar
from agent.providers import ProveedorChat, TemplateProvider
from agent.rag import Buscador, SinEmbeddings, expandir_siglas
from agent.router import clasificar, temas_rag
from agent.tools import HerramientasMock
from tests.agent.dobles import ChatFijo

TCEA = 2137  # fragmento de la Res. SBS 3274-2017 que define la tasa de costo efectivo anual


def buscador_que_apunta_a(i: int) -> Buscador:
    """Un buscador cuya consulta es exactamente el vector del fragmento `i`."""
    b = Buscador()
    b.embeber = lambda _: b.indice.reconstruct(i).reshape(1, -1)
    return b


@pytest.fixture(scope="module")
def tcea():
    return buscador_que_apunta_a(TCEA)


def test_el_indice_de_diego_carga_completo():
    b = Buscador()
    assert b.indice.ntotal == len(b.fragmentos) == 3761
    assert b.indice.d == 768


def test_encuentra_el_fragmento_y_trae_su_fuente(tcea):
    r = tcea.buscar("¿qué es la TCEA?", ["deudas"])
    assert r[0]["id"] == f"frag-{TCEA}"
    assert r[0]["institucion"] and r[0]["titulo"].startswith("Reglamento de Gestion")
    assert "similitud" not in r[0]


def test_el_filtro_de_modulo_excluye_otros_modulos(tcea):
    assert all(f["modulo"] == "derechos" for f in tcea.buscar("x", ["derechos"]))
    assert all(f["id"] != f"frag-{TCEA}" for f in tcea.buscar("x", ["derechos"]))


def test_bajo_el_umbral_no_devuelve_nada():
    b = Buscador()
    b.embeber = lambda _: np.zeros((1, 768), dtype=np.float32)
    assert b.buscar("¿quién ganó el partido?") == []


def test_expande_siglas_una_sola_vez():
    assert expandir_siglas("TCEA y tcea") == "TCEA (tasa de costo efectivo anual) y tcea"


@pytest.mark.parametrize(
    "pregunta, modulos",
    [
        ("¿Qué es la TCEA?", ["deudas"]),
        ("¿Qué derechos tengo si me cobran de más?", ["derechos"]),
        ("¿Cómo funciona la CTS?", ["laboral"]),
        ("¿Qué es el fenómeno El Niño?", ["fenomeno_el_nino"]),
        ("¿Qué significa liquidez?", None),
    ],
)
def test_router_manda_a_educacion_con_su_modulo(pregunta, modulos):
    assert clasificar(pregunta)[0] == "educacion"
    assert temas_rag(pregunta)[0] == modulos


@pytest.mark.parametrize("pregunta", ["¿Cuál es mi perfil?", "¿Qué es el tipo de cambio?"])
def test_educacion_no_le_quita_preguntas_a_otras_intenciones(pregunta):
    assert clasificar(pregunta)[0] != "educacion"


def test_respuesta_educativa_por_plantilla_cita_y_trae_la_fuente(tcea):
    agente = construir(HerramientasMock(), [TemplateProvider()], espera_s=0, buscador=tcea)
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Qué es la TCEA?"})
    assert r["intent"] == "educacion"
    assert f"[fuente: frag-{TCEA}]" in r["answer"]
    assert r["verified"] is True
    assert r["sources"][0]["id"] == f"frag-{TCEA}"
    assert r["sources"][0]["context"] == "Peru"
    assert r["figures"] == []  # los números de la norma no son cifras del cliente


def test_guia_de_eeuu_lleva_su_aviso():
    b = Buscador()
    i = next(
        i
        for i, f in enumerate(b.fragmentos)
        if f["contexto"] != "Peru" and f["modulo"] == "salud_financiera"
    )
    agente = construir(
        HerramientasMock(), [TemplateProvider()], 0, buscador=buscador_que_apunta_a(i)
    )
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Qué es un presupuesto?"})
    assert "las normas peruanas pueden ser distintas" in r["answer"]
    assert r["sources"][0]["context"] != "Peru"


def test_sin_buscador_ni_evidencia_no_inventa():
    agente = construir(HerramientasMock(), [TemplateProvider()], espera_s=0)
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Qué es la TCEA?"})
    assert r["intent"] == "sin_fuente" and r["sources"] == []


def test_sin_ollama_para_embeddings_no_inventa():
    b = Buscador()

    def caido(_):
        raise SinEmbeddings("ConnectError")

    b.embeber = caido
    agente = construir(HerramientasMock(), [TemplateProvider()], espera_s=0, buscador=b)
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Qué es la TCEA?"})
    assert r["intent"] == "sin_fuente"


def test_llm_que_cita_un_fragmento_que_no_trajo_termina_en_plantilla(tcea):
    chat = ChatFijo("La TCEA incluye todos los costos del crédito [fuente: frag-1].")
    cadena = [ProveedorChat("falso", chat, (Exception,)), TemplateProvider()]
    # Se fuerza el paso por el LLM (por defecto educación va directo a plantilla).
    agente = construir(HerramientasMock(), cadena, 0, solo_plantilla=set(), buscador=tcea)
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Qué es la TCEA?"})
    assert r["provider"] == "plantilla"
    assert f"frag-{TCEA}" in r["answer"]


# JF-04, parte que faltaba: números del fragmento citado.

FRAGMENTOS = {"frag-1": "Según el artículo 11 de la Ley 29571, el plazo es de 30 días."}


def test_acepta_numeros_del_fragmento_citado():
    texto = "Tienes 30 días según el artículo 11 [fuente: frag-1]."
    assert juzgar(texto, {}, fragmentos=FRAGMENTOS, exigir_cita=True).ok


def test_no_acepta_numeros_de_un_fragmento_que_no_cita():
    assert not juzgar("Tienes 30 días para reclamar.", {}, fragmentos=FRAGMENTOS).ok


def test_exigir_cita_rechaza_respuesta_sin_fuente():
    v = juzgar("La TCEA incluye todos los costos.", {}, fragmentos=FRAGMENTOS, exigir_cita=True)
    assert not v.ok
