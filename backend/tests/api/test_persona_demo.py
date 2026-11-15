"""`demo-001` debe decir lo mismo que el motor del front. La prueba de que los JSON siguen al motor está en
frontend/pruebas/demo001.test.js; aquí se comprueba que la API sirve esos JSON y que no se contradicen entre sí."""
import json

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.comun.rutas import DATA_SAMPLE, ruta

client = TestClient(app)
BASE = "/api/v1/customers/demo-001"


def _guardado(nombre: str) -> dict:
    with open(ruta(DATA_SAMPLE, "demo-001", nombre), encoding="utf-8") as archivo:
        return json.load(archivo)


@pytest.mark.parametrize(
    ("ruta_api", "archivo"),
    [("health", "health.json"), ("events", "events.json"), ("recommendations", "recommendations.json")],
)
def test_la_api_sirve_lo_que_genera_el_motor(ruta_api, archivo):
    assert client.get(f"{BASE}/{ruta_api}").json() == _guardado(archivo)


def test_el_pronostico_es_el_del_motor():
    assert client.get(f"{BASE}/forecast").json() == _guardado("forecast.json")


def test_el_pronostico_recortado_es_el_inicio_del_guardado():
    guardado = _guardado("forecast.json")["forecast"]

    assert client.get(f"{BASE}/forecast?days=5").json()["forecast"] == guardado[:5]


def test_el_dia_de_riesgo_es_el_primero_con_peor_caso_negativo():
    data = client.get(f"{BASE}/forecast").json()
    negativos = [p["date"] for p in data["forecast"] if p["lower_bound"] < 0]

    assert data["first_risk_date"] == negativos[0]


def test_responder_no_modifica_lo_compartido():
    primera = client.get(f"{BASE}/forecast?days=3").json()
    primera["forecast"].clear()

    assert len(client.get(f"{BASE}/forecast?days=3").json()["forecast"]) == 3
