import json

import httpx
import pytest
from google.genai.errors import ClientError

from agent import providers
from agent.providers import ProveedorChat, TemplateProvider, redactar_con_respaldo
from agent.tools import HerramientasMock
from tests.agent.dobles import ChatFijo, ChatQueFalla

DATOS = {"get_forecast": HerramientasMock().get_forecast("c-001")}


def gemini_con(chat):
    real = providers.gemini("clave-falsa")
    return ProveedorChat("gemini", chat, real.errores)


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("sin red"),
        httpx.ReadTimeout("timeout"),
        ClientError(
            429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
        ),
    ],
)
def test_gemini_caido_reintenta_una_vez_y_responde_plantilla(error):
    chat = ChatQueFalla(error)
    texto, proveedor = redactar_con_respaldo(
        [gemini_con(chat), TemplateProvider()], "pronostico", DATOS, espera_s=0
    )
    assert chat.llamadas == 2
    assert proveedor == "plantilla"
    assert "S/ 210" in texto


def test_gemini_real_con_red_apagada_responde_plantilla(monkeypatch):
    def sin_red(*args, **kwargs):
        raise httpx.ConnectError("red apagada")

    monkeypatch.setattr(httpx.Client, "send", sin_red)
    monkeypatch.setattr(httpx.AsyncClient, "send", sin_red)
    _, proveedor = redactar_con_respaldo(
        [providers.gemini("clave-falsa"), TemplateProvider()], "pronostico", DATOS, espera_s=0
    )
    assert proveedor == "plantilla"


def test_al_proveedor_solo_le_llegan_salidas_de_tools_sin_identificadores():
    chat = ChatFijo("ok")
    gemini_con(chat).redactar("pronostico", DATOS)
    enviado = json.dumps(chat.recibidos, ensure_ascii=False)
    assert "c-001" not in enviado
    assert "customer_id" not in enviado
    assert "210.0" in enviado


def test_al_llm_le_llega_solo_el_ultimo_dia_del_pronostico():
    chat = ChatFijo("ok")
    gemini_con(chat).redactar("pronostico", DATOS)
    enviado = json.dumps(chat.recibidos, ensure_ascii=False)
    # 980 es la banda alta del primer día: no debe llegarle, así no la mezcla con el último.
    assert "980" not in enviado and "-310.0" in enviado


def test_cadena_por_defecto_es_ollama_y_plantilla(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert [p.nombre for p in providers.cadena_desde_entorno()] == ["ollama", "plantilla"]


def test_gemini_sin_clave_se_omite(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert [p.nombre for p in providers.cadena_desde_entorno()] == ["ollama", "plantilla"]


def test_gemini_con_clave_va_detras_de_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "clave-falsa")
    assert [p.nombre for p in providers.cadena_desde_entorno()] == ["ollama", "gemini", "plantilla"]


def test_modo_plantilla_no_usa_llm(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "plantilla")
    assert [p.nombre for p in providers.cadena_desde_entorno()] == ["plantilla"]


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("", "http://localhost:11434"),
        ("0.0.0.0:11434", "http://localhost:11434"),
        ("http://0.0.0.0:11434", "http://localhost:11434"),
        ("192.168.1.20:11434", "http://192.168.1.20:11434"),
        ("http://localhost:11434", "http://localhost:11434"),
    ],
)
def test_host_ollama_se_normaliza(monkeypatch, valor, esperado):
    monkeypatch.setenv("OLLAMA_HOST", valor)
    assert providers.host_ollama() == esperado
