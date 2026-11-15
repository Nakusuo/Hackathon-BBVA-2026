from datetime import datetime

from fastapi import APIRouter, HTTPException, Response

from src.agente_analitico import datos_vivos
from src.api.agente import cliente_de_la_base
from src.api.schemas.expenses import (
    ExpenseCreateRequest,
    ExpenseCreateResponse,
)

router = APIRouter(prefix="/api/v1/customers", tags=["Expenses"])


@router.post("/{customer_id}/expenses", response_model=ExpenseCreateResponse, status_code=201)
def create_expense(customer_id: str, request: ExpenseCreateRequest, response: Response):
    cliente = cliente_de_la_base(customer_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        registro = datos_vivos.registrar(
            cliente,
            "gasto",
            float(request.amount),
            categoria=request.category,
            fecha=request.date,
            id_mov=request.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    if registro["duplicado"]:
        response.status_code = 200

    return {
        "id": registro["id"],
        "customer_id": customer_id,
        "amount": registro["monto"],
        "currency": request.currency,
        "category": registro["categoria"],
        "date": datetime.fromisoformat(registro["fecha"]).date(),
        "created_at": datetime.fromisoformat(registro["registrado_en"]).astimezone(),
        "duplicate": registro["duplicado"],
    }
