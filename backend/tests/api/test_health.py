
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_system_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "lucas-api"
    }


def test_financial_health_success():
    response = client.get(
        "/api/v1/customers/demo-001/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["score"] == 72
    assert data["status"] == "estable"
    assert data["quadrant"] == "Q2"
    assert data["emergency_fund_months"] == 1.5
    assert data["currency"] == "PEN"


def test_financial_health_not_found():
    response = client.get(
        "/api/v1/customers/demo-999/health"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )
