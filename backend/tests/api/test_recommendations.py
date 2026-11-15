
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

BASE_URL = "/api/v1/customers"


def test_recommendations_success():
    response = client.get(
        f"{BASE_URL}/demo-001/recommendations"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["currency"] == "PEN"
    assert isinstance(data["recommendations"], list)


def test_recommendations_max_three():
    response = client.get(
        f"{BASE_URL}/demo-001/recommendations"
    )

    assert response.status_code == 200

    recommendations = response.json()["recommendations"]

    assert len(recommendations) <= 3


def test_recommendations_structure():
    response = client.get(
        f"{BASE_URL}/demo-001/recommendations"
    )

    assert response.status_code == 200

    recommendations = response.json()["recommendations"]
    assert len(recommendations) > 0

    required_fields = {
        "id",
        "action",
        "estimated_impact",
        "impact_type",
        "impact_period",
        "reason",
        "data_used",
        "assumptions",
        "confidence",
        "disclaimer",
    }

    for recommendation in recommendations:
        assert required_fields.issubset(recommendation.keys())
        assert recommendation["estimated_impact"] >= 0
        assert recommendation["confidence"] in {
            "alta", "media", "baja"
        }


def test_recommendations_disclaimer():
    response = client.get(
        f"{BASE_URL}/demo-001/recommendations"
    )

    assert response.status_code == 200

    for recommendation in response.json()["recommendations"]:
        assert "tú decides" in (
            recommendation["disclaimer"].lower()
        )


def test_recommendations_not_found():
    response = client.get(
        f"{BASE_URL}/demo-999/recommendations"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )
