
from fastapi import APIRouter, HTTPException

from src.api.schemas.health import FinancialHealthResponse


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Financial Health"]
)

# Datos sintéticos temporales para probar el contrato.
DEMO_CUSTOMERS = {
    "demo-001": {
        "customer_id": "demo-001",
        "score": 72,
        "status": "estable",
        "quadrant": "Q2",
        "emergency_fund_months": 1.5,
        "currency": "PEN"
    }
}


@router.get(
    "/{customer_id}/health",
    response_model=FinancialHealthResponse
)
def get_financial_health(customer_id: str):
    customer = DEMO_CUSTOMERS.get(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    return customer
