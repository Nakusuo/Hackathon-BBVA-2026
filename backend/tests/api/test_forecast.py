
from datetime import date, timedelta

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_forecast_success():
    response = client.get(
        "/api/v1/customers/demo-001/forecast"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert data["currency"] == "PEN"
    assert data["horizon_days"] == 30
    assert data["confidence_level"] == 0.80
    assert len(data["forecast"]) == 30


def test_forecast_data_structure():
    response = client.get(
        "/api/v1/customers/demo-001/forecast"
    )

    assert response.status_code == 200

    forecast = response.json()["forecast"]

    for point in forecast:
        assert "date" in point
        assert "predicted_balance" in point
        assert "lower_bound" in point
        assert "upper_bound" in point

        assert (
            point["lower_bound"]
            <= point["predicted_balance"]
            <= point["upper_bound"]
        )


def test_forecast_dates():
    response = client.get(
        "/api/v1/customers/demo-001/forecast"
    )

    assert response.status_code == 200

    forecast = response.json()["forecast"]
    today = date.today()

    for index, point in enumerate(forecast, start=1):
        expected_date = today + timedelta(days=index)

        assert point["date"] == expected_date.isoformat()


def test_forecast_not_found():
    response = client.get(
        "/api/v1/customers/demo-999/forecast"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Cliente no encontrado"
    )
