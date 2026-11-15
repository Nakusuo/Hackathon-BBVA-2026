from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

# Restricción de demostración, NO sustituye autenticación real.
def customer_scope(db: Session, customer_id: str):
    if customer_id != "demo-001":
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.execute(text("SELECT set_config('app.customer_id', :cid, true)"), {"cid": customer_id})
    exists = db.execute(text("SELECT 1 FROM app.perfil WHERE customer_id=:cid"), {"cid": customer_id}).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
