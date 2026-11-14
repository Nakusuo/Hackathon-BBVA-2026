
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"]
)


@router.post(
    "/chat",
    response_model=ChatResponse
)
def send_message(request: ChatRequest):
    if request.customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    conversation_id = (
        request.conversation_id
        or f"conv-{uuid4().hex[:12]}"
    )

    # Respuesta simulada para MG-03.
    # No se consulta un modelo de IA.
    answer = (
        "Soy Lucas, tu asistente financiero. "
        "Esta es una respuesta de demostración. "
        "Puedo ayudarte a explorar opciones para "
        "organizar tus gastos y establecer metas "
        "de ahorro. Por ahora no estoy analizando "
        "tus datos financieros reales."
    )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "provider": "mock",
        "verified": False,
        "sources": [],
        "tools_used": []
    }
