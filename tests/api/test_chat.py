"""POST /api/v1/chat: la ruta traduce la respuesta del agente al contrato. El agente real se prueba en tests/test_agente.py;
aquí se cambia por uno de respuesta fija para no cargar modelos ni datos."""
import pytest
from fastapi.testclient import TestClient

from src.api.agente import Agente, obtener_agente
from src.api.main import app

BASE_URL = "/api/v1/chat"
RESPUESTA = {"respuesta": "Hola, Constructor.\nEn 30 dias tu saldo ronda S/ 2,000.\nTu decides.", "proveedor": "plantilla", "intencion": "pronostico", "cifras_sin_respaldo": [],
             "citas": [{"titulo": "Guia de la CTS", "pagina": 2, "documento": "cts.pdf", "enlace": ""}],
             "trazas": ["cargar_contexto", "router:pronostico", "agente:pronostico", "agente:salud", "finalizar"]}


class RepoFalso:
    pos = {"C00016": 0}


@pytest.fixture
def client(monkeypatch):
    vistos = []

    def responder_falso(grafo, customer_id, mensaje):
        vistos.append((customer_id, mensaje))
        return {**RESPUESTA, **grafo}

    monkeypatch.setattr("src.agente_analitico.grafo.responder", responder_falso)
    agente = Agente(RepoFalso(), {}, {"demo-001": "C00016", "independiente": "C00016"})
    app.dependency_overrides[obtener_agente] = lambda: agente
    cliente = TestClient(app)
    cliente.agente, cliente.vistos = agente, vistos
    yield cliente
    app.dependency_overrides.clear()


def mensaje(**cambios):
    return {"customer_id": "demo-001", "message": "¿Llego a fin de mes?", **cambios}


def test_responde_con_los_campos_del_contrato(client):
    data = client.post(BASE_URL, json=mensaje()).json()
    assert data["conversation_id"].startswith("conv-")
    assert data["answer"] == "En 30 dias tu saldo ronda S/ 2,000." and data["provider"] == "plantilla" and data["intent"] == "pronostico"
    assert data["tools_used"] == ["pronostico", "salud"]
    assert data["sources"] == [{"id": "cts.pdf", "title": "Guia de la CTS", "page": 2, "url": None}]


@pytest.mark.parametrize("alias", ["demo-001", "independiente", "C00016"])
def test_el_id_del_front_se_traduce_al_cliente_de_la_base(client, alias):
    assert client.post(BASE_URL, json=mensaje(customer_id=alias)).status_code == 200
    assert client.vistos == [("C00016", "¿Llego a fin de mes?")]


def test_una_cifra_sin_respaldo_deja_la_respuesta_sin_verificar(client):
    assert client.post(BASE_URL, json=mensaje()).json()["verified"] is True
    client.agente.grafo = {"cifras_sin_respaldo": [999.0]}
    assert client.post(BASE_URL, json=mensaje()).json()["verified"] is False


def test_conserva_la_conversacion_y_crea_una_distinta_cada_vez(client):
    assert client.post(BASE_URL, json=mensaje(conversation_id="conv-prueba-001")).json()["conversation_id"] == "conv-prueba-001"
    primera, segunda = (client.post(BASE_URL, json=mensaje()).json()["conversation_id"] for _ in range(2))
    assert primera != segunda


def test_cliente_que_no_existe(client):
    respuesta = client.post(BASE_URL, json=mensaje(customer_id="demo-999"))
    assert respuesta.status_code == 404 and respuesta.json()["detail"] == "Cliente no encontrado"
    assert client.vistos == []


@pytest.mark.parametrize("cambios", [{"message": ""}, {"customer_id": ""}, {"message": "a" * 501}])
def test_pedido_invalido(client, cambios):
    assert client.post(BASE_URL, json=mensaje(**cambios)).status_code == 422


def test_falta_el_mensaje(client):
    assert client.post(BASE_URL, json={"customer_id": "demo-001"}).status_code == 422


def test_el_saludo_conserva_el_hola_y_las_demas_respuestas_no_lo_repiten(client):
    client.agente.grafo = {"intencion": "saludo", "respuesta": "Hola, Constructor. Soy Lucas.\nPuedo ver si llegas a fin de mes. Tu decides."}
    assert client.post(BASE_URL, json=mensaje()).json()["answer"] == "Hola, Constructor. Soy Lucas.\nPuedo ver si llegas a fin de mes."
