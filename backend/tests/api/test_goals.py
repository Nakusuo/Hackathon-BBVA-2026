
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers.goals import ahorro_quincenal_sugerido

client = TestClient(app)

BASE_URL = "/api/v1/customers"

MOCKS = Path(__file__).resolve().parents[3] / "data" / "sample" / "mocks"


def leer_mock(nombre):
    return json.loads((MOCKS / nombre).read_text(encoding="utf-8"))


MONTOS = {
    "target_amount",
    "current_amount",
    "suggested_biweekly_saving",
    "projected_year_end_savings",
}


def como_numeros(meta):
    """Pasa los montos a float: Pydantic serializa Decimal como texto."""
    return {
        clave: float(valor) if clave in MONTOS and valor is not None else valor
        for clave, valor in meta.items()
    }


def test_goals_coincide_con_mock():
    response = client.get(f"{BASE_URL}/demo-001/goals")

    assert response.status_code == 200

    data = response.json()
    mock = leer_mock("goals.json")

    assert data["customer_id"] == mock["customer_id"]
    assert data["currency"] == mock["currency"]
    assert [como_numeros(meta) for meta in data["goals"]] == mock["goals"]


def test_create_goal_con_request_del_mock():
    response = client.post(
        f"{BASE_URL}/demo-001/goals",
        json=leer_mock("goal-request.json")
    )

    assert response.status_code == 201

    data = como_numeros(response.json())
    mock = leer_mock("goal-created.json")

    assert set(data) == set(mock)
    calculados = {"id", "suggested_biweekly_saving", "projected_year_end_savings", "completion_probability"}
    for clave in set(mock) - calculados:
        assert data[clave] == mock[clave]
    assert data["suggested_biweekly_saving"] > 0


def test_ahorro_quincenal_sugerido():
    sugerido = ahorro_quincenal_sugerido(
        Decimal(3000),
        Decimal(600),
        date(2027, 6, 30),
        hoy=date(2026, 11, 1),
    )

    assert sugerido == Decimal("150.00")


def test_ahorro_quincenal_con_fecha_vencida():
    sugerido = ahorro_quincenal_sugerido(
        Decimal(1000),
        Decimal(400),
        date(2026, 1, 1),
        hoy=date(2026, 11, 1),
    )

    assert sugerido == Decimal("600.00")


def test_goals_success():
    response = client.get(
        f"{BASE_URL}/demo-001/goals"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert isinstance(data["goals"], list)
    assert len(data["goals"]) == 2


def test_goals_structure():
    response = client.get(
        f"{BASE_URL}/demo-001/goals"
    )

    assert response.status_code == 200

    required_fields = {
        "id",
        "name",
        "target_amount",
        "current_amount",
        "target_date",
        "progress_percentage",
    }

    for goal in response.json()["goals"]:
        assert required_fields.issubset(goal.keys())
        date.fromisoformat(goal["target_date"])


def test_goals_amounts():
    response = client.get(
        f"{BASE_URL}/demo-001/goals"
    )

    assert response.status_code == 200

    for goal in response.json()["goals"]:
        target = Decimal(str(goal["target_amount"]))
        current = Decimal(str(goal["current_amount"]))

        assert target > 0
        assert current >= 0


def test_goals_progress():
    response = client.get(
        f"{BASE_URL}/demo-001/goals"
    )

    assert response.status_code == 200

    for goal in response.json()["goals"]:
        target = Decimal(str(goal["target_amount"]))
        current = Decimal(str(goal["current_amount"]))

        expected = (current / target) * 100

        assert goal["progress_percentage"] == float(
            expected
        )


def test_goals_not_found():
    response = client.get(
        f"{BASE_URL}/demo-999/goals"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )


def test_create_goal_success():
    response = client.post(
        f"{BASE_URL}/demo-001/goals",
        json={
            "name": "Comprar una laptop",
            "target_amount": 5000,
            "currency": "PEN",
            "target_date": "2027-06-30"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"].startswith("goal-")
    assert data["name"] == "Comprar una laptop"
    assert Decimal(str(data["target_amount"])) == 5000
    assert Decimal(str(data["current_amount"])) == 0
    assert data["progress_percentage"] == 0


@pytest.mark.parametrize("amount", [0, -100])
def test_create_goal_invalid_amount(amount):
    response = client.post(
        f"{BASE_URL}/demo-001/goals",
        json={
            "name": "Meta de prueba",
            "target_amount": amount,
            "currency": "PEN",
            "target_date": "2027-06-30"
        }
    )

    assert response.status_code == 422


def test_create_goal_invalid_currency():
    response = client.post(
        f"{BASE_URL}/demo-001/goals",
        json={
            "name": "Meta de prueba",
            "target_amount": 1000,
            "currency": "USD",
            "target_date": "2027-06-30"
        }
    )

    assert response.status_code == 422


def test_create_goal_invalid_date():
    response = client.post(
        f"{BASE_URL}/demo-001/goals",
        json={
            "name": "Meta de prueba",
            "target_amount": 1000,
            "currency": "PEN",
            "target_date": "fecha-invalida"
        }
    )

    assert response.status_code == 422


def test_create_goal_empty_name():
    response = client.post(
        f"{BASE_URL}/demo-001/goals",
        json={
            "name": "",
            "target_amount": 1000,
            "currency": "PEN",
            "target_date": "2027-06-30"
        }
    )

    assert response.status_code == 422


def test_create_goal_not_found():
    response = client.post(
        f"{BASE_URL}/demo-999/goals",
        json={
            "name": "Meta de prueba",
            "target_amount": 1000,
            "currency": "PEN",
            "target_date": "2027-06-30"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )


def test_create_goal_unique_ids():
    payload = {
        "name": "Meta de prueba",
        "target_amount": 1000,
        "currency": "PEN",
        "target_date": "2027-06-30"
    }

    first = client.post(
        f"{BASE_URL}/demo-001/goals",
        json=payload
    )

    second = client.post(
        f"{BASE_URL}/demo-001/goals",
        json=payload
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] != second.json()["id"]


def test_create_goal_with_initial_savings():
    payload = {
        "name": "Comprar una laptop",
        "target_amount": 5000,
        "current_amount": 1500,
        "currency": "PEN",
        "target_date": "2027-06-30"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 201

    data = response.json()

    assert float(data["current_amount"]) == 1500
    assert data["progress_percentage"] == 30.0


def test_create_goal_without_initial_savings():
    payload = {
        "name": "Fondo de emergencia",
        "target_amount": 3000,
        "currency": "PEN",
        "target_date": "2027-12-31"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 201

    data = response.json()

    assert float(data["current_amount"]) == 0
    assert data["progress_percentage"] == 0.0


def test_create_goal_negative_initial_savings():
    payload = {
        "name": "Viaje",
        "target_amount": 4000,
        "current_amount": -500,
        "currency": "PEN",
        "target_date": "2027-08-30"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 422


def test_create_goal_half_completed():
    payload = {
        "name": "Estudios",
        "target_amount": 2000,
        "current_amount": 1000,
        "currency": "PEN",
        "target_date": "2027-09-30"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 201
    assert response.json()["progress_percentage"] == 50.0


def test_create_goal_fully_completed():
    payload = {
        "name": "Meta completada",
        "target_amount": 1000,
        "current_amount": 1000,
        "currency": "PEN",
        "target_date": "2027-12-31"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 201
    assert response.json()["progress_percentage"] == 100.0


def test_create_goal_savings_exceed_target():
    payload = {
        "name": "Laptop",
        "target_amount": 1000,
        "current_amount": 1500,
        "currency": "PEN",
        "target_date": "2027-12-31"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 422


def test_create_goal_savings_equal_target():
    payload = {
        "name": "Meta completada",
        "target_amount": 1000,
        "current_amount": 1000,
        "currency": "PEN",
        "target_date": "2027-12-31"
    }

    response = client.post(
        "/api/v1/customers/demo-001/goals",
        json=payload
    )

    assert response.status_code == 201
    assert response.json()["progress_percentage"] == 100.0
