
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from src.api.schemas.forecast import ForecastResponse


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Forecast"]
)


@router.get(
    "/{customer_id}/forecast",
    response_model=ForecastResponse
)
def get_forecast(customer_id: str):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Datos sintéticos para probar el endpoint.
    # Todavía no existe un modelo predictivo conectado.
    start_date = date.today()

    forecast_points = []

    for day in range(1, 31):
        predicted_balance = 1500 - (day * 10)

        forecast_points.append({
            "date": start_date + timedelta(days=day),
            "predicted_balance": predicted_balance,
            "lower_bound": predicted_balance - 100,
            "upper_bound": predicted_balance + 100
        })

    return {
        "customer_id": customer_id,
        "currency": "PEN",
        "horizon_days": 30,
        "confidence_level": 0.80,
        "forecast": forecast_points
    }
