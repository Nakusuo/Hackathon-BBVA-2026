from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.financial_data import financial_snapshot
from src.api.schemas.recommendations import RecommendationsResponse
from decimal import Decimal

router=APIRouter(prefix='/api/v1/customers',tags=['Recommendations'])

@router.get('/{customer_id}/recommendations',response_model=RecommendationsResponse)
def get_recommendations(customer_id:str,db:Session=Depends(get_db)):
    try: s=financial_snapshot(db,customer_id)
    except HTTPException as e:
        if e.status_code==503: return {'customer_id':customer_id,'currency':'PEN','recommendations':[]}
        raise
    items=[]
    if s['expenses'] > 0 and s['expenses'] >= s['income'] * Decimal('0.75'):
        saving=round(float(s['expenses'])*0.05,2)
        items.append({'id':'reduce-expenses-5pct','action':'Revisar gastos mensuales para reducirlos un 5%',
        'estimated_impact':saving,'impact_type':'expense_reduction','impact_period':'mensual',
        'reason':'Los gastos registrados representan una parte elevada de los ingresos.',
        'data_used':['monthly_income','monthly_expenses',s['source']],
        'assumptions':['Una reducción hipotética del 5% es viable; requiere revisión del usuario'],
        'confidence':'baja','disclaimer':'Regla orientativa; no constituye asesoría financiera.'})
    if s['income']>s['expenses']+s['debt'] and s['cushion']<3:
        surplus=float(s['income']-s['expenses']-s['debt']); amount=round(surplus*0.1,2)
        if amount>0: items.append({'id':'build-emergency-fund','action':'Separar el 10% del excedente mensual para emergencias',
        'estimated_impact':amount,'impact_type':'savings_allocation','impact_period':'mensual',
        'reason':'El colchón de emergencia estimado es inferior a tres meses.',
        'data_used':['monthly_income','monthly_expenses','current_savings',s['source']],
        'assumptions':['El excedente mensual se mantiene estable'], 'confidence':'baja',
        'disclaimer':'Recomendación basada en reglas, no en un modelo entrenado.'})
    return {'customer_id':customer_id,'currency':'PEN','recommendations':items[:3]}
