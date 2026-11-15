
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
    assert 0 <= data["score"] <= 100
    assert data["quadrant"] in {"Q1", "Q2", "Q3", "Q4"}
    assert data["emergency_fund_months"] >= 0
    assert data["currency"] == "PEN"


def test_financial_health_not_found():
    response = client.get(
        "/api/v1/customers/demo-999/health"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )
