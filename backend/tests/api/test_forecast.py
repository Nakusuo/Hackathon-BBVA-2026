import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from src.api.agente import ClienteDesconocido
from src.api.main import app
from src.comun.rutas import MODELOS, ruta

client = TestClient(app)


@pytest.fixture(autouse=True)
def sin_modelo(request, monkeypatch):
    """Por defecto la ruta usa el respaldo; las pruebas marcadas con `modelo_real` usan lo que haya en la máquina."""
    if "modelo_real" not in request.keywords:
        monkeypatch.setattr("src.api.routers.forecast._pronostico_real", lambda cid, dias: None)


def test_forecast_success():
    response = client.get("/api/v1/customers/demo-001/forecast")

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["currency"] == "PEN"
    assert data["horizon_days"] == 30
    assert data["confidence_level"] == 0.80
    assert len(data["forecast"]) == 30


def test_forecast_data_structure():
    response = client.get("/api/v1/customers/demo-001/forecast")

    assert response.status_code == 200

    forecast = response.json()["forecast"]

    for point in forecast:
        assert "date" in point
        assert "predicted_balance" in point
        assert "lower_bound" in point
        assert "upper_bound" in point

        assert point["lower_bound"] <= point["predicted_balance"] <= point["upper_bound"]


def test_forecast_dates():
    response = client.get("/api/v1/customers/demo-001/forecast")

    assert response.status_code == 200

    forecast = response.json()["forecast"]
    today = date.today()

    for index, point in enumerate(forecast, start=1):
        expected_date = today + timedelta(days=index)

        assert point["date"] == expected_date.isoformat()


def test_forecast_not_found():
    response = client.get("/api/v1/customers/demo-999/forecast")

    assert response.status_code == 404
    assert response.json()["detail"] == ("Cliente no encontrado")


def test_forecast_respaldo_se_declara_muestra():
    data = client.get("/api/v1/customers/demo-001/forecast").json()

    assert data["sample_only"] is True
    assert data["synthetic_data"] is True
    assert data["model"] is None


@pytest.mark.parametrize("days", [1, 7, 30])
def test_forecast_acepta_days(days):
    data = client.get(f"/api/v1/customers/demo-001/forecast?days={days}").json()

    assert data["horizon_days"] == days
    assert len(data["forecast"]) == days


@pytest.mark.parametrize("days", [0, 31, "abc"])
def test_forecast_days_fuera_de_rango(days):
    response = client.get(f"/api/v1/customers/demo-001/forecast?days={days}")

    assert response.status_code == 422


def test_forecast_usa_el_pronostico_del_modelo(monkeypatch):
    real = {
        "customer_id": "C00016",
        "currency": "PEN",
        "horizon_days": 2,
        "confidence_level": 0.8,
        "forecast": [
            {
                "date": "2026-11-16",
                "predicted_balance": 900.0,
                "lower_bound": 700.0,
                "upper_bound": 1100.0,
            },
            {
                "date": "2026-11-17",
                "predicted_balance": 400.0,
                "lower_bound": 100.0,
                "upper_bound": 700.0,
            },
        ],
        "first_risk_date": "2026-11-17",
        "model": "lightgbm-cuantil-conformal-serie-diaria-v1",
        "data_as_of": "2026-11-15",
        "risk_probability": 0.42,
        "synthetic_data": True,
        "sample_only": False,
    }
    pedidos = []

    def falso(cid, dias):
        pedidos.append((cid, dias))
        return real

    monkeypatch.setattr("src.api.routers.forecast._pronostico_real", falso)
    data = client.get("/api/v1/customers/demo-001/forecast?days=2").json()

    assert pedidos == [("demo-001", 2)]
    assert data["customer_id"] == "demo-001"
    assert data["first_risk_date"] == "2026-11-17"
    assert data["model"].startswith("lightgbm")
    assert data["sample_only"] is False
    assert data["forecast"][0]["predicted_balance"] == 900.0


def test_forecast_cliente_desconocido_del_agente(monkeypatch):
    def desconocido(cid, dias):
        raise ClienteDesconocido(cid)

    monkeypatch.setattr("src.api.routers.forecast._pronostico_real", desconocido)

    assert client.get("/api/v1/customers/zzz/forecast").status_code == 404


@pytest.mark.modelo_real
@pytest.mark.skipif(
    not (
        os.path.isdir(ruta("data", "generado"))
        and os.path.exists(os.path.join(MODELOS, "serie_diaria.pkl"))
    ),
    reason="faltan los datos generados o el modelo de serie diaria",
)
def test_forecast_con_modelo_real():
    data = client.get("/api/v1/customers/demo-001/forecast?days=10").json()

    assert data["model"].startswith("lightgbm")
    assert data["sample_only"] is False
    assert len(data["forecast"]) == 10
    assert all(
        p["lower_bound"] <= p["predicted_balance"] <= p["upper_bound"] for p in data["forecast"]
    )
