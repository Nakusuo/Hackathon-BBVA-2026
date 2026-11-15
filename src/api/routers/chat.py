from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from src.api.agente import Agente, ClienteDesconocido, obtener_agente
from src.api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1", tags=["Chat"])


# `def` y no `async def`: el agente bloquea mientras redacta el modelo local, y así FastAPI lo corre en un hilo aparte.
@router.post("/chat", response_model=ChatResponse)
def send_message(request: ChatRequest, agente: Agente = Depends(obtener_agente)):
    try:
        respuesta = agente.responder(request.customer_id, request.message)
    except ClienteDesconocido:
        raise HTTPException(status_code=404, detail="Cliente no encontrado") from None
    return {"conversation_id": request.conversation_id or f"conv-{uuid4().hex[:12]}", **respuesta}
