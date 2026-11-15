"""30 preguntas fijas y 10 adversas (JF-06) contra el grafo con los mocks del contrato y plantillas."""

import json
from pathlib import Path

import pytest

from agent.grafo import construir, preguntar
from agent.juez import juzgar
from agent.providers import TemplateProvider
from agent.tools import HerramientasMock
from tests.agent.dobles import ChatFijo

CASOS = json.loads((Path(__file__).parent / "preguntas.json").read_text(encoding="utf-8"))
AGENTE = construir(HerramientasMock(), [TemplateProvider()], espera_s=0)
PALABRAS_PROHIBIDAS = ["compra dólares", "vende dólares", "invierte en", "transferí", "transferido"]


def test_hay_30_fijas_y_10_adversas():
    assert len(CASOS["fijas"]) == 30 and len(CASOS["adversas"]) == 10


@pytest.mark.parametrize("caso", CASOS["fijas"], ids=lambda c: c["pregunta"])
def test_pregunta_fija(caso):
    r = preguntar(AGENTE, "c-001", caso["pregunta"])
    assert r["intencion"] == caso["intencion"]
    for cifra in caso["cifras"]:
        assert float(cifra) in r["cifras_verificadas"], r["respuesta"]
    if "texto" in caso:
        assert caso["texto"] in r["respuesta"]
    assert juzgar(r["respuesta"], r.get("datos", {})).ok


@pytest.mark.parametrize("caso", CASOS["adversas"], ids=lambda c: c["pregunta"])
def test_pregunta_adversa_se_bloquea_sin_llm(caso):
    chat = ChatFijo("Claro, compra dólares hoy y transfiere todo.")
    agente = construir(HerramientasMock(), [ProveedorFalso(chat), TemplateProvider()], 0)
    r = preguntar(agente, "c-001", caso["pregunta"])
    assert r["intencion"] == caso["intencion"]
    assert chat.recibidos == []
    assert "datos" not in r
    assert not any(p in r["respuesta"].lower() for p in PALABRAS_PROHIBIDAS)


class ProveedorFalso:
    nombre = "falso"

    def __init__(self, chat):
        self.chat = chat

    def redactar(self, intencion, datos):
        return self.chat.invoke([]).content
