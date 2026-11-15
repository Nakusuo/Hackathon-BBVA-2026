from fastapi import APIRouter, HTTPException

from src.api.persona_demo import ID_DEMO, respuesta
from src.api.schemas.events import EventsResponse

router = APIRouter(prefix="/api/v1/customers", tags=["Financial Events"])


@router.get("/{customer_id}/events", response_model=EventsResponse)
def get_financial_events(customer_id: str):
    if customer_id != ID_DEMO:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    # No se envían notificaciones reales.
    return respuesta("events.json")
