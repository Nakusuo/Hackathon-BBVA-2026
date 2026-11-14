
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from src.api.schemas.events import EventsResponse


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Financial Events"]
)


@router.get(
    "/{customer_id}/events",
    response_model=EventsResponse
)
def get_financial_events(customer_id: str):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Eventos sintéticos para probar el contrato.
    # No se envían notificaciones reales.
    today = date.today()

    return {
        "customer_id": customer_id,
        "events": [
            {
                "id": "evt-001",
                "type": "recurring_expense",
                "title": "Próximo pago recurrente",
                "message": (
                    "Tienes un pago recurrente "
                    "de S/ 80 registrado para los "
                    "próximos días."
                ),
                "event_date": today + timedelta(days=3),
                "priority": "medium",
                "estimated_impact": -80.0,
                "notified": False
            },
            {
                "id": "evt-002",
                "type": "income",
                "title": "Próximo ingreso",
                "message": (
                    "Se ha registrado un ingreso "
                    "estimado de S/ 1500."
                ),
                "event_date": today + timedelta(days=7),
                "priority": "low",
                "estimated_impact": 1500.0,
                "notified": False
            }
        ],
        "weekly_notifications_remaining": 3
    }
