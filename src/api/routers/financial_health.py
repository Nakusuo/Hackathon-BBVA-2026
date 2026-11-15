from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.financial_data import financial_snapshot
from src.api.schemas.health import FinancialHealthResponse
router=APIRouter(prefix='/api/v1/customers',tags=['Financial Health'])

@router.get('/{customer_id}/health',response_model=FinancialHealthResponse)
def get_financial_health(customer_id:str,db:Session=Depends(get_db)):
    s=financial_snapshot(db,customer_id)
    # Puntuación HEURÍSTICA explicable, no modelo bancario validado.
    cushion=float(s['cushion']); ratio=float(s['ratio'])
    score=max(0,min(100,round(35+min(cushion,6)*8-max(ratio,0)*45+(15 if s['income']>=s['expenses']+s['debt'] else -15))))
    if score>=75: quadrant='Q1'
    elif score>=50: quadrant='Q2'
    elif score>=25: quadrant='Q3'
    else: quadrant='Q4'
    return {'customer_id':customer_id,'score':score,'status':'estable' if score>=50 else 'en_riesgo','quadrant':quadrant,'emergency_fund_months':round(max(0,cushion),2),'currency':'PEN'}
