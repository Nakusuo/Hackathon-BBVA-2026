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
    pos = {"C00016": 0, "C00168": 1}


@pytest.fixture
def client(monkeypatch):
    vistos = []

    def responder_falso(grafo, customer_id, mensaje):
        vistos.append((customer_id, mensaje))
        return {**RESPUESTA, **grafo}

    monkeypatch.setattr("src.agente_analitico.grafo.responder", responder_falso)
    agente = Agente(RepoFalso(), {}, {"demo-001": "C00016", "independiente": "C00016", "formal": "C00168"})
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
    client.agente.grafo = {"intencion": "conversacion", "respuesta": "Hola, Constructor. Soy Lucas.\nPuedo ver si llegas a fin de mes. Tu decides."}
    assert client.post(BASE_URL, json=mensaje()).json()["answer"] == "Hola, Constructor. Soy Lucas.\nPuedo ver si llegas a fin de mes."


def test_las_opciones_llegan_como_botones_y_el_menu_escrito_se_quita(client):
    opciones = [{"id": "pronostico", "texto": "¿Llego a fin de mes?", "pregunta": "¿Llego a fin de mes con mi plata?"},
                {"id": "salud_nivel", "texto": "Mi salud financiera", "pregunta": "¿Cómo está mi salud financiera?"}]
    client.agente.grafo = {"intencion": "conversacion", "opciones": opciones,
                           "respuesta": "¡Hola, Constructor! Elige una opcion: ¿Llego a fin de mes? • Mi salud financiera ¿Por donde empezamos? Tu decides."}
    data = client.post(BASE_URL, json=mensaje()).json()
    assert data["answer"] == "¡Hola, Constructor! Elige una opcion: ¿Por donde empezamos?"
    assert data["options"] == [{"id": "pronostico", "label": "¿Llego a fin de mes?", "question": "¿Llego a fin de mes con mi plata?"},
                               {"id": "salud_nivel", "label": "Mi salud financiera", "question": "¿Cómo está mi salud financiera?"}]


def test_la_conversacion_recuerda_la_ultima_pregunta_con_tema_y_no_mezcla_conversaciones(client):
    client.agente.grafo = {"intencion": "meta"}
    client.post(BASE_URL, json=mensaje(message="quiero ahorrar para un carro de 12 mil", conversation_id="conv-a"))
    client.post(BASE_URL, json=mensaje(message="¿y en 6 meses?", conversation_id="conv-a"))
    client.post(BASE_URL, json=mensaje(message="¿y en 6 meses?", conversation_id="conv-b"))
    assert [m for _, m in client.vistos] == ["quiero ahorrar para un carro de 12 mil", "¿y en 6 meses? quiero ahorrar para un carro de 12 mil", "¿y en 6 meses?"]


def test_la_propuesta_de_meta_viaja_con_los_nombres_del_contrato(client):
    assert client.post(BASE_URL, json=mensaje()).json()["goal_proposal"] is None
    client.agente.grafo = {"intencion": "meta", "propuesta_meta": {"nombre": "Viaje a Cusco", "objetivo": 2800.0, "fecha": "2027-05-14"}}
    assert client.post(BASE_URL, json=mensaje()).json()["goal_proposal"] == {"name": "Viaje a Cusco", "target": 2800.0, "date": "2027-05-14"}


def test_la_memoria_no_mezcla_clientes_con_el_mismo_id_de_conversacion_y_no_crece_sin_fin(client):
    from src.api.agente import LARGO_RECORDADO
    client.agente.grafo = {"intencion": "meta"}
    client.post(BASE_URL, json=mensaje(customer_id="independiente", message="quiero ahorrar para un carro de 12 mil", conversation_id="conv-x"))
    client.post(BASE_URL, json=mensaje(customer_id="formal", message="¿y en 6 meses?", conversation_id="conv-x"))
    assert client.vistos[-1] == ("C00168", "¿y en 6 meses?")
    for _ in range(20):
        client.post(BASE_URL, json=mensaje(customer_id="independiente", message="¿y en 6 meses?", conversation_id="conv-x"))
    assert all(len(v) <= LARGO_RECORDADO for v in client.agente._previas.values())
    assert client.vistos[-1][1].startswith("¿y en 6 meses?") and "carro de 12 mil" not in client.vistos[-1][1][LARGO_RECORDADO + 20:]
