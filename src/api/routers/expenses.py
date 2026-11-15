from fastapi import APIRouter,Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.db_context import customer_scope
from src.api.schemas.expenses import ExpenseCreateRequest,ExpenseCreateResponse
router=APIRouter(prefix="/api/v1/customers",tags=["Expenses"])

@router.post("/{customer_id}/expenses",response_model=ExpenseCreateResponse,status_code=201)
def create_expense(customer_id:str,request:ExpenseCreateRequest,db:Session=Depends(get_db)):
    customer_scope(db,customer_id)
    try:
        r=db.execute(text("INSERT INTO app.movimientos_usuario(customer_id,fecha,monto,tipo,categoria,comercio) VALUES(:cid,:fecha,:monto,'gasto',:categoria,:comercio) RETURNING id,creado_en"),{"cid":customer_id,"fecha":request.date,"monto":request.amount,"categoria":request.category,"comercio":request.description}).mappings().one()
        db.commit()
    except Exception:
        db.rollback();raise
    return {"id":f"expense-{r['id']}","customer_id":customer_id,"amount":request.amount,"currency":request.currency,"category":request.category,"description":request.description,"date":request.date,"created_at":r['creado_en']}
