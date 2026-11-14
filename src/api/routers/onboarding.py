
from fastapi import APIRouter, HTTPException

from src.api.schemas.onboarding import (
    OnboardingRequest,
    OnboardingResponse,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Onboarding"]
)

CLIENTES_DEMO = {"demo-001", "demo-002"}


@router.post(
    "/onboarding",
    response_model=OnboardingResponse
)
def create_onboarding(request: OnboardingRequest):
    if request.customer_id not in CLIENTES_DEMO:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # El perfil lo asigna el modelo DI-12; hasta conectarlo no se inventa uno.
    return {
        "customer_id": request.customer_id,
        "profile": {
            "segment": "pending_model_assignment",
            "quadrant": None
        },
        "confidence": None,
        "model": "pending-di-12",
        "is_estimate": True
    }
