
from decimal import Decimal

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

BASE_URL = "/api/v1/customers"


def test_offers_success():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["currency"] == "PEN"
    assert isinstance(data["offers"], list)


def test_offers_maximum_three():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    offers = response.json()["offers"]

    assert len(offers) <= 3


def test_offers_structure():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    required_fields = {
        "id",
        "name",
        "category",
        "description",
        "reason",
        "estimated_benefit",
        "eligible",
        "disclaimer",
    }

    for offer in response.json()["offers"]:
        assert required_fields.issubset(offer.keys())


def test_offers_eligible():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    for offer in response.json()["offers"]:
        assert offer["eligible"] is True


def test_offers_non_negative_benefit():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    for offer in response.json()["offers"]:
        benefit = Decimal(
            str(offer["estimated_benefit"])
        )

        assert benefit >= 0


def test_offers_no_term_savings():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    categories = {
        offer["category"]
        for offer in response.json()["offers"]
    }

    # El perfil demo tiene un fondo de
    # emergencia inferior a tres meses.
    assert "term_savings" not in categories


def test_offers_no_credit():
    response = client.get(
        f"{BASE_URL}/demo-001/offers"
    )

    assert response.status_code == 200

    categories = {
        offer["category"]
        for offer in response.json()["offers"]
    }

    # El catálogo sintético no debe
    # incluir ofertas de crédito.
    assert "credit" not in categories


def test_offers_not_found():
    response = client.get(
        f"{BASE_URL}/demo-999/offers"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )
