
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.api.schemas.expenses import (
    ExpenseCreateRequest,
    ExpenseCreateResponse,
)


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Expenses"]
)


@router.post(
    "/{customer_id}/expenses",
    response_model=ExpenseCreateResponse,
    status_code=201
)
def create_expense(
    customer_id: str,
    request: ExpenseCreateRequest
):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Registro simulado para MG-03.
    # No se almacena en PostgreSQL.
    expense_id = f"expense-{uuid4().hex[:8]}"

    return {
        "id": expense_id,
        "customer_id": customer_id,
        "amount": request.amount,
        "currency": request.currency,
        "category": request.category,
        "description": request.description,
        "date": request.date,
        "created_at": datetime.now(timezone.utc)
    }
