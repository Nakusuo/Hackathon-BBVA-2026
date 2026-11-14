
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from src.api.schemas.goals import (
    GoalsResponse,
    GoalCreateRequest,
    GoalCreateResponse,
)


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Savings Goals"]
)


@router.get(
    "/{customer_id}/goals",
    response_model=GoalsResponse
)
def get_savings_goals(customer_id: str):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Datos sintéticos para validar el contrato.
    # No se consulta PostgreSQL.
    return {
        "customer_id": customer_id,
        "goals": [
            {
                "id": "goal-001",
                "name": "Comprar una laptop",
                "target_amount": "5000.00",
                "current_amount": "1500.00",
                "currency": "PEN",
                "target_date": (
                    date.today() + timedelta(days=180)
                ),
                "progress_percentage": 30.0
            },
            {
                "id": "goal-002",
                "name": "Fondo de emergencia",
                "target_amount": "3000.00",
                "current_amount": "750.00",
                "currency": "PEN",
                "target_date": (
                    date.today() + timedelta(days=365)
                ),
                "progress_percentage": 25.0
            }
        ]
    }


from uuid import uuid4


@router.post(
    "/{customer_id}/goals",
    response_model=GoalCreateResponse,
    status_code=201
)
def create_savings_goal(
    customer_id: str,
    request: GoalCreateRequest
):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Registro simulado para MG-03.
    # No se almacena en PostgreSQL.
    goal_id = f"goal-{uuid4().hex[:8]}"

    return {
        "id": goal_id,
        "customer_id": customer_id,
        "name": request.name,
        "target_amount": request.target_amount,
        "current_amount": request.current_amount,
        "currency": request.currency,
        "target_date": request.target_date,
        "progress_percentage": float(
    (request.current_amount / request.target_amount) * 100
)
    }
