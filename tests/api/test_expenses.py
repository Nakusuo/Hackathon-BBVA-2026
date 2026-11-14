
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

BASE_URL = "/api/v1/customers"


def valid_expense():
    return {
        "amount": 45.90,
        "currency": "PEN",
        "category": "alimentacion",
        "description": "Almuerzo",
        "date": "2026-11-14"
    }


def test_create_expense_success():
    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=valid_expense()
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"].startswith("expense-")
    assert data["customer_id"] == "demo-001"
    assert Decimal(str(data["amount"])) == Decimal("45.90")
    assert data["currency"] == "PEN"
    assert data["category"] == "alimentacion"
    assert data["description"] == "Almuerzo"
    assert data["date"] == "2026-11-14"


def test_create_expense_timestamp():
    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=valid_expense()
    )

    assert response.status_code == 201

    created_at = datetime.fromisoformat(
        response.json()["created_at"].replace("Z", "+00:00")
    )

    assert created_at.tzinfo is not None


@pytest.mark.parametrize("amount", [0, -50])
def test_create_expense_invalid_amount(amount):
    payload = valid_expense()
    payload["amount"] = amount

    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=payload
    )

    assert response.status_code == 422


def test_create_expense_invalid_currency():
    payload = valid_expense()
    payload["currency"] = "USD"

    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=payload
    )

    assert response.status_code == 422


def test_create_expense_invalid_date():
    payload = valid_expense()
    payload["date"] = "fecha-invalida"

    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=payload
    )

    assert response.status_code == 422


def test_create_expense_empty_category():
    payload = valid_expense()
    payload["category"] = ""

    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=payload
    )

    assert response.status_code == 422


def test_create_expense_optional_description():
    payload = valid_expense()
    payload.pop("description")

    response = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=payload
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_expense_not_found():
    response = client.post(
        f"{BASE_URL}/demo-999/expenses",
        json=valid_expense()
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )


def test_create_expense_unique_ids():
    first = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=valid_expense()
    )

    second = client.post(
        f"{BASE_URL}/demo-001/expenses",
        json=valid_expense()
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] != second.json()["id"]
