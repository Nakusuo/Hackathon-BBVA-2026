from fastapi import APIRouter,Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.db_context import customer_scope
from src.api.schemas.events import EventsResponse
router=APIRouter(prefix="/api/v1/customers",tags=["Financial Events"])
TYPES={"ingreso":"income","gratificacion":"gratification","cts":"cts","gasto_recurrente":"recurring_expense","riesgo_saldo_negativo":"negative_balance_risk"}
PRIORITIES={"baja":"low","media":"medium","alta":"high","low":"low","medium":"medium","high":"high"}
@router.get("/{customer_id}/events",response_model=EventsResponse)
def get_financial_events(customer_id:str,db:Session=Depends(get_db)):
    customer_scope(db,customer_id)
    rows=db.execute(text("SELECT id,tipo,urgencia,fecha_evento,mensaje,impacto_soles FROM app.avisos WHERE customer_id=:cid ORDER BY fecha_evento,id"),{"cid":customer_id}).mappings().all()
    events=[]
    for r in rows:
        event_type=TYPES.get(r['tipo'],r['tipo'])
        priority=PRIORITIES.get(r['urgencia'])
        if event_type not in TYPES.values() or priority is None or r['fecha_evento'] is None:
            continue  # Contrato actual no representa estos tipos de avisos
        events.append({"id":f"evt-{r['id']}","type":event_type,"title":event_type.replace('_',' ').capitalize(),"message":r['mensaje'],"event_date":r['fecha_evento'],"priority":priority,"estimated_impact":float(r['impacto_soles'] or 0),"notified":False})
    return {"customer_id":customer_id,"events":events,"weekly_notifications_remaining":3}
