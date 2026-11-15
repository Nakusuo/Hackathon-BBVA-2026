
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

URL = "/api/v1/fx"


def test_fx_success():
    response = client.get(URL)

    assert response.status_code == 200

    data = response.json()

    assert data["base"] == "USD"
    assert data["quote"] == "PEN"


def test_fx_rate():
    response = client.get(URL)

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["rate"]) == Decimal("3.75")
    assert Decimal(data["rate"]) > 0


def test_fx_synthetic_source():
    response = client.get(URL)

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "synthetic_demo"
    assert data["is_fallback"] is True
    assert data["is_stale"] is True


def test_fx_date():
    response = client.get(URL)

    assert response.status_code == 200

    data = response.json()

    assert date.fromisoformat(data["date"]) == date(
        2026, 1, 1
    )


def test_fx_explicit_currencies():
    response = client.get(
        URL,
        params={"base": "USD", "quote": "PEN"}
    )

    assert response.status_code == 200


def test_fx_invalid_base():
    response = client.get(
        URL,
        params={"base": "EUR", "quote": "PEN"}
    )

    assert response.status_code == 422


def test_fx_invalid_quote():
    response = client.get(
        URL,
        params={"base": "USD", "quote": "EUR"}
    )

    assert response.status_code == 422
