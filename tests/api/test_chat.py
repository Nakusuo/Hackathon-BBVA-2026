
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)

BASE_URL = "/api/v1/chat"


def valid_message():
    return {
        "customer_id": "demo-001",
        "message": "¿Cómo puedo mejorar mis ahorros?",
        "conversation_id": None
    }


def test_chat_success():
    response = client.post(
        BASE_URL,
        json=valid_message()
    )

    assert response.status_code == 200

    data = response.json()

    assert data["conversation_id"].startswith("conv-")
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0


def test_chat_response_structure():
    response = client.post(
        BASE_URL,
        json=valid_message()
    )

    assert response.status_code == 200

    required_fields = {
        "conversation_id",
        "answer",
        "provider",
        "verified",
        "sources",
        "tools_used",
    }

    assert required_fields.issubset(
        response.json().keys()
    )


def test_chat_mock_provider():
    response = client.post(
        BASE_URL,
        json=valid_message()
    )

    assert response.status_code == 200

    data = response.json()

    assert data["provider"] == "mock"
    assert data["verified"] is False
    assert data["sources"] == []
    assert data["tools_used"] == []


def test_chat_existing_conversation():
    payload = valid_message()
    payload["conversation_id"] = "conv-prueba-001"

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 200

    assert (
        response.json()["conversation_id"]
        == "conv-prueba-001"
    )


def test_chat_new_conversation_ids():
    first = client.post(
        BASE_URL,
        json=valid_message()
    )

    second = client.post(
        BASE_URL,
        json=valid_message()
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        first.json()["conversation_id"]
        != second.json()["conversation_id"]
    )


def test_chat_empty_message():
    payload = valid_message()
    payload["message"] = ""

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_chat_empty_customer():
    payload = valid_message()
    payload["customer_id"] = ""

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_chat_customer_not_found():
    payload = valid_message()
    payload["customer_id"] = "demo-999"

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )


def test_chat_missing_message():
    payload = valid_message()
    payload.pop("message")

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422


def test_chat_without_conversation_id():
    payload = valid_message()
    payload.pop("conversation_id")

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"].startswith(
        "conv-"
    )
