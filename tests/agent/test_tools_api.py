"""JF-03: tools sobre la API del contrato, probadas con un servidor falso que sirve los mocks."""

import json

import httpx
import pytest

from agent.chat import responder
from agent.grafo import construir
from agent.providers import TemplateProvider
from agent.tools import RUTA_MOCKS, HerramientaNoDisponible, HerramientasAPI

RUTAS = {
    ("GET", "/api/v1/customers/demo-001/health"): "health",
    ("GET", "/api/v1/customers/demo-001/forecast"): "forecast",
    ("GET", "/api/v1/customers/demo-001/recommendations"): "recommendations",
    ("POST", "/api/v1/simulations"): "simulation",
    ("GET", "/api/v1/fx"): "fx",
}


def api_falsa(pedidos: list | None = None, estado: int = 200):
    def manejar(request: httpx.Request) -> httpx.Response:
        if pedidos is not None:
            pedidos.append(request)
        nombre = RUTAS.get((request.method, request.url.path))
        if nombre is None:
            return httpx.Response(404, json={"detail": "no existe"})
        cuerpo = json.loads((RUTA_MOCKS / f"{nombre}.json").read_text(encoding="utf-8"))
        return httpx.Response(estado, json=cuerpo)

    cliente = httpx.Client(base_url="http://api", transport=httpx.MockTransport(manejar))
    return HerramientasAPI(cliente=cliente)


def test_cada_tool_llama_a_su_endpoint_del_contrato():
    tools = api_falsa()
    assert tools.get_health("demo-001")["score"] == 72
    assert tools.get_forecast("demo-001")["first_risk_date"] == "2026-11-18"
    assert len(tools.get_recos("demo-001")["recommendations"]) == 3
    assert tools.get_fx()["base"] == "USD"


def test_simulate_manda_un_gasto_unico_y_devuelve_lo_que_pidio():
    pedidos = []
    respuesta = api_falsa(pedidos).simulate("demo-001", 150.0)
    cuerpo = json.loads(pedidos[0].content)
    assert cuerpo["changes"] == [
        {
            "type": "expense",
            "amount": 150.0,
            "frequency": "once",
            "description": "Gasto consultado en el chat",
        }
    ]
    assert respuesta["request"]["changes"][0]["amount"] == 150.0
    assert "simulated" in respuesta


def test_customer_id_raro_no_cambia_la_ruta():
    pedidos = []
    with pytest.raises(HerramientaNoDisponible):
        api_falsa(pedidos).get_health("../fx")
    assert pedidos[0].url.raw_path.decode() == "/api/v1/customers/..%2Ffx/health"


@pytest.mark.parametrize("estado", [404, 500, 503])
def test_error_de_la_api_es_herramienta_no_disponible(estado):
    with pytest.raises(HerramientaNoDisponible):
        api_falsa(estado=estado).get_health("demo-001")


def test_api_caida_responde_sin_cifras_y_no_se_rompe():
    def caida(request):
        raise httpx.ConnectError("sin servidor")

    tools = HerramientasAPI(cliente=httpx.Client(transport=httpx.MockTransport(caida)))
    agente = construir(tools, [TemplateProvider()], espera_s=0)
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Llego a fin de mes?"})
    assert r["intent"] == "sin_datos"
    assert r["verified_figures"] == [] and r["figures"] == []
    assert "no puedo ver tus datos" in r["answer"]


@pytest.mark.parametrize(
    "pregunta, cifra",
    [
        ("¿Llego a fin de mes?", 210.0),
        ("¿Puedo gastar S/ 150?", 150.0),
        ("¿Cómo está mi salud financiera?", 72.0),
        ("¿Qué me conviene hacer?", 120.0),
    ],
)
def test_agente_de_punta_a_punta_con_la_api(pregunta, cifra):
    agente = construir(api_falsa(), [TemplateProvider()], espera_s=0)
    r = responder(agente, {"customer_id": "demo-001", "message": pregunta})
    assert r["verified"] is True
    assert cifra in r["verified_figures"]


def test_cada_cifra_del_pronostico_lleva_su_etiqueta_aunque_se_repita_en_la_serie():
    # En la API de Miguel el 1 300 es máximo del último día y mínimo de otro día.
    serie = [
        {
            "date": "2026-12-13",
            "predicted_balance": 1400.0,
            "lower_bound": 1300.0,
            "upper_bound": 1500.0,
        },
        {
            "date": "2026-12-14",
            "predicted_balance": 1200.0,
            "lower_bound": 1100.0,
            "upper_bound": 1300.0,
        },
    ]
    pronostico = {"horizon_days": 30, "confidence_level": 0.8, "forecast": serie}

    class Tools(HerramientasAPI):
        def get_forecast(self, customer_id):
            return pronostico

    agente = construir(Tools(cliente=httpx.Client()), [TemplateProvider()], espera_s=0)
    r = responder(agente, {"customer_id": "demo-001", "message": "¿Llego a fin de mes?"})
    etiquetas = {f["text"]: f["label"] for f in r["figures"]}
    assert etiquetas["S/ 1 100"] == "Saldo mínimo probable"
    assert etiquetas["S/ 1 300"] == "Saldo máximo probable"
