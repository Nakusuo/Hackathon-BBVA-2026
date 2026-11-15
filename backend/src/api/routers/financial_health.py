from fastapi import APIRouter, HTTPException

from src.api.persona_demo import ID_DEMO, respuesta
from src.api.schemas.health import FinancialHealthResponse

router = APIRouter(prefix="/api/v1/customers", tags=["Financial Health"])


@router.get("/{customer_id}/health", response_model=FinancialHealthResponse)
def get_financial_health(customer_id: str):
    if customer_id != ID_DEMO:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return respuesta("health.json")
