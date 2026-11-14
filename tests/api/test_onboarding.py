import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

BASE_URL = "/api/v1/onboarding"

MOCKS = Path(__file__).resolve().parents[2] / "data" / "sample" / "mocks"


def leer_mock(nombre):
    return json.loads((MOCKS / nombre).read_text(encoding="utf-8"))


def test_onboarding_con_request_del_mock():
    response = client.post(
        BASE_URL,
        json=leer_mock("onboarding-request.json")
    )

    assert response.status_code == 200
    assert response.json() == leer_mock("onboarding.json")


def valid_onboarding():
    return {
        "customer_id": "demo-001",
        "answers": {
            "monthly_income": 2500,
            "monthly_expenses": 1500,
            "current_savings": 3000,
            "monthly_debt_payment": 300,
            "income_stability": "stable"
        }
    }


def test_onboarding_success():
    response = client.post(
        BASE_URL,
        json=valid_onboarding()
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["profile"] == {
        "segment": "pending_model_assignment",
        "quadrant": None
    }
    assert data["confidence"] is None
    assert data["model"] == "pending-di-12"
    assert data["is_estimate"] is True


def test_onboarding_response_structure():
    response = client.post(
        BASE_URL,
        json=valid_onboarding()
    )

    assert response.status_code == 200

    required_fields = {
        "customer_id",
        "profile",
        "confidence",
        "model",
        "is_estimate",
    }

    assert required_fields.issubset(
        response.json().keys()
    )


@pytest.mark.parametrize(
    "field",
    [
        "monthly_income",
        "monthly_expenses",
        "current_savings",
        "monthly_debt_payment",
    ]
)
def test_onboarding_negative_amount(field):
    payload = valid_onboarding()
    payload["answers"][field] = -100

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_onboarding_invalid_stability():
    payload = valid_onboarding()
    payload["answers"]["income_stability"] = "unknown"

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_onboarding_missing_answer():
    payload = valid_onboarding()
    payload["answers"].pop("monthly_expenses")

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_onboarding_missing_answers():
    payload = valid_onboarding()
    payload.pop("answers")

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_onboarding_empty_customer():
    payload = valid_onboarding()
    payload["customer_id"] = ""

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_onboarding_customer_not_found():
    payload = valid_onboarding()
    payload["customer_id"] = "demo-999"

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )


def test_onboarding_zero_amounts():
    payload = valid_onboarding()

    payload["answers"]["monthly_income"] = 0
    payload["answers"]["monthly_expenses"] = 0
    payload["answers"]["current_savings"] = 0
    payload["answers"]["monthly_debt_payment"] = 0

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 200
