from fastapi import APIRouter, HTTPException

from src.api.persona_demo import ID_DEMO, respuesta
from src.api.schemas.recommendations import RecommendationsResponse

router = APIRouter(prefix="/api/v1/customers", tags=["Recommendations"])


@router.get("/{customer_id}/recommendations", response_model=RecommendationsResponse)
def get_recommendations(customer_id: str):
    if customer_id != ID_DEMO:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return respuesta("recommendations.json")
