from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.db_context import customer_scope
from src.api.schemas.chat import ChatRequest,ChatResponse
router=APIRouter(prefix="/api/v1",tags=["Chat"])
@router.post("/chat",response_model=ChatResponse)
def send_message(request:ChatRequest,db:Session=Depends(get_db)):
    customer_scope(db,request.customer_id)
    # La tabla app.mensajes no tiene conversation_id; no se puede persistir ese vínculo todavía.
    # Sin agente conectado, devolver 503 evita presentar respuestas sintéticas como IA real.
    raise HTTPException(status_code=503,detail="Agente de IA pendiente de integración")
