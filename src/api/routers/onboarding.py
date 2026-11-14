
from fastapi import APIRouter, HTTPException

from src.api.schemas.onboarding import (
    OnboardingRequest,
    OnboardingResponse,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Onboarding"]
)


@router.post(
    "/onboarding",
    response_model=OnboardingResponse
)
def create_onboarding(request: OnboardingRequest):
    if request.customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Validación inicial para MG-03.
    # La clasificación depende del modelo de Diego.
    # No asignamos perfiles financieros arbitrarios.
    return {
        "customer_id": request.customer_id,
        "profile": None,
        "confidence": None,
        "model": "pending-integration",
        "is_estimate": True
    }
