
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

URL = "/api/v1/simulations"


def test_simulation_success():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "horizon_days": 30,
        "changes": []
    })

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["currency"] == "PEN"
    assert data["horizon_days"] == 30
    assert len(data["baseline"]["forecast"]) == 30
    assert len(data["simulated"]["forecast"]) == 30
    assert data["difference"] == 0


def test_simulation_expense():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "horizon_days": 30,
        "changes": [
            {
                "type": "expense",
                "amount": 200,
                "frequency": "once",
                "description": "Compra de audífonos"
            }
        ]
    })

    assert response.status_code == 200

    data = response.json()

    assert data["baseline"]["final_balance"] == 1200
    assert data["simulated"]["final_balance"] == 1000
    assert data["difference"] == -200


def test_simulation_income():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "horizon_days": 30,
        "changes": [
            {
                "type": "income",
                "amount": 500,
                "frequency": "once",
                "description": "Ingreso adicional"
            }
        ]
    })

    assert response.status_code == 200
    assert response.json()["difference"] == 500


def test_simulation_monthly_expense():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "horizon_days": 60,
        "changes": [
            {
                "type": "expense",
                "amount": 100,
                "frequency": "monthly",
                "description": "Suscripción mensual"
            }
        ]
    })

    assert response.status_code == 200
    assert response.json()["difference"] == -200


@pytest.mark.parametrize("amount", [0, -100])
def test_simulation_invalid_amount(amount):
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "changes": [
            {
                "type": "expense",
                "amount": amount,
                "frequency": "once",
                "description": "Gasto inválido"
            }
        ]
    })

    assert response.status_code == 422


def test_simulation_invalid_frequency():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "changes": [
            {
                "type": "expense",
                "amount": 100,
                "frequency": "weekly",
                "description": "Gasto semanal"
            }
        ]
    })

    assert response.status_code == 422


def test_simulation_invalid_horizon():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "horizon_days": 0,
        "changes": []
    })

    assert response.status_code == 422


def test_simulation_not_found():
    response = client.post(URL, json={
        "customer_id": "demo-999",
        "changes": []
    })

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )


def test_simulation_disclaimer():
    response = client.post(URL, json={
        "customer_id": "demo-001",
        "changes": []
    })

    assert response.status_code == 200
    assert "tú decides" in (
        response.json()["disclaimer"].lower()
    )
