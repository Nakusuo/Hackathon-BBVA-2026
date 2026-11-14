
from fastapi import APIRouter, HTTPException

from src.api.schemas.recommendations import (
    RecommendationsResponse,
)

router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Recommendations"]
)


@router.get(
    "/{customer_id}/recommendations",
    response_model=RecommendationsResponse,
)
def get_recommendations(customer_id: str):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado",
        )

    # Respuesta sintética basada en el contrato MG-01.
    # No representa una recomendación calculada.
    return {
        "customer_id": customer_id,
        "currency": "PEN",
        "recommendations": [
            {
                "id": "rec-001",
                "action": "Reducir gastos de delivery",
                "estimated_impact": 120.0,
                "impact_type": "expense_reduction",
                "impact_period": "monthly",
                "reason": (
                    "Se identificaron gastos frecuentes "
                    "en delivery"
                ),
                "data_used": ["transactions"],
                "assumptions": [
                    "Reducir dos pedidos por semana"
                ],
                "confidence": "media",
                "disclaimer": (
                    "Esta es una simulación. Tú decides."
                ),
            }
        ],
    }
