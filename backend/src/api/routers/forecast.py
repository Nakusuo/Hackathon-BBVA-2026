import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from src.api.agente import ClienteDesconocido, obtener_agente
from src.api.schemas.forecast import ForecastResponse

log = logging.getLogger("lucas.api.forecast")

router = APIRouter(prefix="/api/v1/customers", tags=["Forecast"])


def _pronostico_real(customer_id: str, days: int) -> dict | None:
    """Pronóstico del modelo entrenado. None si faltan los modelos o los datos: entonces la ruta responde el mock."""
    from src.agente_analitico.contrato import pronostico_contrato

    try:
        agente = obtener_agente()
        return pronostico_contrato(agente.repo, agente.cliente(customer_id), days)
    except ClienteDesconocido:
        raise
    except (
        Exception
    ):  # sin datos o modelos en esta máquina la API sigue respondiendo con el respaldo
        log.warning("Pronóstico real no disponible, se usa el respaldo", exc_info=True)
        return None


def _pronostico_respaldo(customer_id: str, days: int) -> dict:
    start_date = date.today()
    forecast_points = []

    for day in range(1, days + 1):
        predicted_balance = 1500 - (day * 10)

        forecast_points.append(
            {
                "date": start_date + timedelta(days=day),
                "predicted_balance": predicted_balance,
                "lower_bound": predicted_balance - 100,
                "upper_bound": predicted_balance + 100,
            }
        )

    return {
        "customer_id": customer_id,
        "currency": "PEN",
        "horizon_days": days,
        "confidence_level": 0.80,
        "forecast": forecast_points,
        "synthetic_data": True,
        "sample_only": True,
    }


@router.get("/{customer_id}/forecast", response_model=ForecastResponse)
def get_forecast(customer_id: str, days: int = Query(30, ge=1, le=30)):
    try:
        real = _pronostico_real(customer_id, days)
    except ClienteDesconocido:
        raise HTTPException(status_code=404, detail="Cliente no encontrado") from None

    if real is not None:
        # El contrato devuelve el id real de la base; la persona pidió su alias.
        return {**real, "customer_id": customer_id}

    if customer_id != "demo-001":
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return _pronostico_respaldo(customer_id, days)
