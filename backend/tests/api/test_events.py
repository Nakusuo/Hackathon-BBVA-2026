
from datetime import date

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

BASE_URL = "/api/v1/customers"


def test_events_success():
    response = client.get(
        f"{BASE_URL}/demo-001/events"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert isinstance(data["events"], list)
    assert len(data["events"]) <= 3


def test_events_structure():
    response = client.get(
        f"{BASE_URL}/demo-001/events"
    )

    assert response.status_code == 200

    required_fields = {
        "id",
        "type",
        "title",
        "message",
        "event_date",
        "priority",
        "estimated_impact",
        "notified",
    }

    for event in response.json()["events"]:
        assert required_fields.issubset(event.keys())
        date.fromisoformat(event["event_date"])
        assert event["priority"] in {
            "low", "medium", "high"
        }


def test_events_notification_limit():
    response = client.get(
        f"{BASE_URL}/demo-001/events"
    )

    assert response.status_code == 200

    remaining = response.json()[
        "weekly_notifications_remaining"
    ]

    assert 0 <= remaining <= 3


def test_events_not_notified():
    response = client.get(
        f"{BASE_URL}/demo-001/events"
    )

    assert response.status_code == 200

    for event in response.json()["events"]:
        assert event["notified"] is False


def test_events_not_found():
    response = client.get(
        f"{BASE_URL}/demo-999/events"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )
