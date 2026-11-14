
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.api.schemas.goals import (
    GoalCreateRequest,
    GoalsResponse,
    SavingsGoal,
)

router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Savings Goals"]
)

DIAS_POR_QUINCENA = 15


def ahorro_quincenal_sugerido(
    target_amount: Decimal,
    current_amount: Decimal,
    target_date: date,
    hoy: date,
) -> Decimal:
    """Reparte lo que falta en las quincenas hasta la fecha límite; mínimo una."""
    quincenas = max(1, (target_date - hoy).days // DIAS_POR_QUINCENA)
    restante = target_amount - current_amount

    return (restante / quincenas).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
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

    # Datos sintéticos iguales a goals.json; no se consulta PostgreSQL.
    return {
        "customer_id": customer_id,
        "currency": "PEN",
        "goals": [
            {
                "id": "goal-001",
                "name": "Fondo de emergencia",
                "target_amount": "3000.00",
                "current_amount": "600.00",
                "target_date": "2027-06-30",
                "progress_percentage": 20.0,
                "suggested_biweekly_saving": "150.00",
                "projected_year_end_savings": "900.00",
                "completion_probability": 0.72
            },
            {
                "id": "goal-002",
                "name": "Comprar una laptop",
                "target_amount": "2500.00",
                "current_amount": "1000.00",
                "target_date": "2027-04-30",
                "progress_percentage": 40.0,
                "suggested_biweekly_saving": "120.00",
                "projected_year_end_savings": "1240.00",
                "completion_probability": 0.81
            }
        ]
    }


@router.post(
    "/{customer_id}/goals",
    response_model=SavingsGoal,
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

    # La proyección anual y la probabilidad salen del pronóstico de DI-06,
    # que aún no está conectado; se devuelven vacías en vez de inventarlas.
    return {
        "id": f"goal-{uuid4().hex[:8]}",
        "name": request.name,
        "target_amount": request.target_amount,
        "current_amount": request.current_amount,
        "target_date": request.target_date,
        "progress_percentage": float(
            request.current_amount / request.target_amount * 100
        ),
        "suggested_biweekly_saving": ahorro_quincenal_sugerido(
            request.target_amount,
            request.current_amount,
            request.target_date,
            date.today(),
        ),
        "projected_year_end_savings": None,
        "completion_probability": None
    }
