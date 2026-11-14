"""Respuesta de POST /api/v1/chat con la forma que se propone para el contrato MG-01."""

from agent.chat import responder
from agent.grafo import construir
from agent.providers import TemplateProvider
from agent.tools import HerramientasMock
from bcrp.servicio import fx_contrato

AGENTE = construir(HerramientasMock(), [TemplateProvider()], espera_s=0)
CAMPOS = {
    "conversation_id",
    "answer",
    "provider",
    "verified",
    "verified_figures",
    "figures",
    "sources",
    "tools_used",
    "intent",
}


def test_respuesta_tiene_los_campos_del_contrato_y_respeta_conversation_id():
    r = responder(
        AGENTE,
        {
            "customer_id": "demo-001",
            "conversation_id": "conv-001",
            "message": "¿Puedo gastar S/ 150 este fin de semana?",
        },
    )
    assert set(r) == CAMPOS
    assert r["conversation_id"] == "conv-001"
    assert r["provider"] == "plantilla"
    assert r["verified"] is True
    assert 150.0 in r["verified_figures"]
    assert r["tools_used"] == ["simulate"]


def test_figures_trae_etiqueta_y_signo_real_para_la_ui():
    r = responder(AGENTE, {"customer_id": "demo-001", "message": "¿Llego a fin de mes?"})
    minimo = {"label": "Saldo mínimo probable", "value": -310.0, "text": "-S/ 310", "unit": "PEN"}
    confianza = {
        "label": "Confianza del pronóstico",
        "value": 80.0,
        "text": "80 %",
        "unit": "percent",
    }
    assert minimo in r["figures"] and confianza in r["figures"]
    # La fecha está verificada, pero no es una cifra que la UI muestre aparte.
    assert all(f["value"] != 18.0 for f in r["figures"])


def test_en_un_empate_gana_la_cifra_del_mismo_signo():
    r = responder(AGENTE, {"customer_id": "demo-001", "message": "¿Puedo gastar S/ 150?"})
    assert r["figures"] == [
        {"label": "Gasto que consultas", "value": 150.0, "text": "S/ 150", "unit": "PEN"},
        {"label": "Saldo final con el gasto", "value": -200.0, "text": "-S/ 200", "unit": "PEN"},
    ]


def test_salud_trae_unidad_de_meses_para_el_colchon():
    r = responder(AGENTE, {"customer_id": "demo-001", "message": "¿Cómo está mi salud?"})
    colchon = next(f for f in r["figures"] if f["label"] == "Meses que cubre tu colchón")
    assert colchon["unit"] == "months"
    puntaje = next(f for f in r["figures"] if f["label"] == "Puntaje de salud")
    assert puntaje["unit"] is None


def test_sin_conversation_id_se_crea_uno():
    r = responder(AGENTE, {"customer_id": "demo-001", "message": "¿Llego a fin de mes?"})
    assert r["conversation_id"].startswith("conv-")


def test_pregunta_bloqueada_no_usa_tools():
    r = responder(AGENTE, {"customer_id": "demo-001", "message": "Compra dólares por mí"})
    assert r["intent"] == "operacion"
    assert r["tools_used"] == []
    assert r["verified"] is True


def test_fx_contrato_marca_el_respaldo():
    grabada = {
        "serie": "tipo_cambio",
        "codigo": "PD04638PD",
        "periodo": "2026-11-12",
        "valor": 3.406,
        "origen": "serie_grabada",
    }
    fx = fx_contrato(grabada)
    assert fx == {
        "base": "USD",
        "quote": "PEN",
        "rate": 3.406,
        "date": "2026-11-12",
        "source": "BCRP PD04638PD",
        "is_fallback": True,
        "is_stale": True,
    }
    assert fx_contrato({**grabada, "origen": "api"})["is_fallback"] is False
