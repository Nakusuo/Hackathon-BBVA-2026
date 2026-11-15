"""El chat de `demo-001` cita las mismas cifras que las pantallas (los JSON del motor del front), no las de un cliente de la base.
El agente se cambia por uno que falla si lo llaman: estas preguntas no pueden pasar por él."""

import json
import re

import pytest
from fastapi.testclient import TestClient
from src.api.agente import Agente, obtener_agente
from src.api.main import app
from src.comun.rutas import DATA_SAMPLE, ruta

URL = "/api/v1/chat"


def _guardado(nombre: str) -> dict:
    with open(ruta(DATA_SAMPLE, "demo-001", nombre), encoding="utf-8") as archivo:
        return json.load(archivo)


class RepoFalso:
    pos = {"C00016": 0}


@pytest.fixture
def client(monkeypatch):
    def agente_prohibido(*_):
        raise AssertionError("demo-001 no debe pasar por el cliente de la base")

    monkeypatch.setattr("src.agente_analitico.grafo.responder", agente_prohibido)
    app.dependency_overrides[obtener_agente] = lambda: Agente(
        RepoFalso(), {}, {"demo-001": "C00016"}
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def preguntar(client, texto: str) -> dict:
    respuesta = client.post(URL, json={"customer_id": "demo-001", "message": texto})
    assert respuesta.status_code == 200
    return respuesta.json()


def montos(texto: str) -> list[float]:
    return [
        float(f"-{m[1]}" if m[0] else m[1])
        for m in re.findall(r"([−-])?S/ ([\d,]+)", texto.replace(",", ""))
    ]


def test_llego_a_mi_cobro_cita_el_pronostico_de_la_pantalla(client):
    r = preguntar(client, "¿Llego a mi cobro?")
    dias = _guardado("forecast.json")["forecast"]
    antes_del_cobro = dias[
        : next(
            i
            for i in range(1, len(dias))
            if dias[i]["predicted_balance"] > dias[i - 1]["predicted_balance"]
        )
    ]
    assert r["verified"] and r["tools_used"] == ["get_forecast"]
    assert montos(r["answer"]) == [
        min(d["predicted_balance"] for d in antes_del_cobro),
        min(d["lower_bound"] for d in antes_del_cobro),
    ]
    assert "el 29 de noviembre" in r["answer"] and "el 30 de noviembre" in r["answer"]


def test_salud_cita_el_puntaje_de_la_pantalla(client):
    r = preguntar(client, "¿cómo está mi salud?")
    salud = _guardado("health.json")
    assert r["verified"] and r["tools_used"] == ["get_health"]
    assert (
        f"{salud['score']} de 100" in r["answer"]
        and f"«{salud['status']}»" in r["answer"]
        and str(salud["emergency_fund_months"]) in r["answer"]
    )


def test_puedo_gastar_150_resta_el_gasto_al_pronostico_de_la_pantalla(client):
    r = preguntar(client, "¿puedo gastar 150?")
    dias = _guardado("forecast.json")["forecast"]
    esperado, peor = (min(d[k] for d in dias[:15]) for k in ("predicted_balance", "lower_bound"))
    assert r["verified"] and r["tools_used"] == ["simulate"]
    assert montos(r["answer"]) == [150, esperado - 150, peor - 150]
    assert "rojo" in r["answer"]


def test_los_tips_son_los_de_la_pantalla(client):
    r = preguntar(client, "¿qué me recomiendas?")
    assert r["verified"] and r["tools_used"] == ["get_recos"]
    assert all(
        t["action"] in r["answer"] for t in _guardado("recommendations.json")["recommendations"]
    )


def test_lo_que_no_esta_en_los_json_no_se_responde_con_otra_persona(client):
    r = preguntar(client, "¿cuánto gasté este mes en comida?")
    assert r["tools_used"] == [] and "no tengo datos" in r["answer"]
    assert not re.search(r"\d", r["answer"])


def test_el_apoyo_no_cita_cifras_de_otro_cliente(client, monkeypatch):
    citando_la_base = {"respuesta": "Tranquilo. Tu saldo es S/ 2,345 y tu salud 71.", "proveedor": "plantilla", "intencion": "apoyo", "cifras_sin_respaldo": [],
                       "citas": [], "trazas": ["agente:pronostico"]}
    monkeypatch.setattr("src.agente_analitico.grafo.responder", lambda *_: citando_la_base)
    r = preguntar(client, "me siento agobiado con la plata")
    assert r["intent"] == "apoyo" and r["verified"] and "2,345" not in r["answer"]
    assert "Estos cambios" not in r["answer"] and "saldo esperado" not in r["answer"]
    assert all(t["action"] in r["answer"] for t in _guardado("recommendations.json")["recommendations"][:1])
