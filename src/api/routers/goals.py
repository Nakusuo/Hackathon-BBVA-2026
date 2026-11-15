from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.db_context import customer_scope
from src.api.schemas.goals import GoalsResponse, GoalCreateRequest, GoalCreateResponse
router=APIRouter(prefix="/api/v1/customers",tags=["Savings Goals"])

@router.get("/{customer_id}/goals",response_model=GoalsResponse)
def get_savings_goals(customer_id:str, db:Session=Depends(get_db)):
    customer_scope(db,customer_id)
    rows=db.execute(text("SELECT id,nombre,monto_objetivo,monto_actual,fecha_objetivo FROM app.metas WHERE customer_id=:cid ORDER BY id"),{"cid":customer_id}).mappings().all()
    return {"customer_id":customer_id,"currency":"PEN","goals":[{"id":f"goal-{r['id']}","name":r['nombre'],"target_amount":r['monto_objetivo'],"current_amount":r['monto_actual'],"currency":"PEN","target_date":r['fecha_objetivo'],"progress_percentage":float(r['monto_actual']/r['monto_objetivo']*100),"suggested_biweekly_saving":None,"projected_year_end_savings":None,"completion_probability":None} for r in rows]}

@router.post("/{customer_id}/goals",response_model=GoalCreateResponse,status_code=201)
def create_savings_goal(customer_id:str,request:GoalCreateRequest,db:Session=Depends(get_db)):
    customer_scope(db,customer_id)
    try:
        r=db.execute(text("INSERT INTO app.metas(customer_id,nombre,monto_objetivo,monto_actual,fecha_objetivo) VALUES(:cid,:name,:target,:current,:date) RETURNING id,nombre,monto_objetivo,monto_actual,fecha_objetivo"),{"cid":customer_id,"name":request.name,"target":request.target_amount,"current":request.current_amount,"date":request.target_date}).mappings().one()
        db.commit()
    except Exception:
        db.rollback();raise
    return {"id":f"goal-{r['id']}","customer_id":customer_id,"name":r['nombre'],"target_amount":r['monto_objetivo'],"current_amount":r['monto_actual'],"currency":"PEN","target_date":r['fecha_objetivo'],"progress_percentage":float(r['monto_actual']/r['monto_objetivo']*100)}
