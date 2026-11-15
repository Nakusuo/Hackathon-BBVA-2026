from datetime import date,timedelta
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.financial_data import financial_snapshot,balance_projection
from src.api.schemas.forecast import ForecastResponse
router=APIRouter(prefix='/api/v1/customers',tags=['Forecast'])

@router.get('/{customer_id}/forecast',response_model=ForecastResponse)
def get_forecast(customer_id:str,db:Session=Depends(get_db)):
    s=financial_snapshot(db,customer_id)
    values=balance_projection(s,30)
    # Banda de incertidumbre ilustrativa, no intervalo estadístico calibrado.
    points=[{'date':date.today()+timedelta(days=i+1),'predicted_balance':v,
        'lower_bound':round(v-abs(v)*0.10,2),'upper_bound':round(v+abs(v)*0.10,2)} for i,v in enumerate(values)]
    return {'customer_id':customer_id,'currency':'PEN','horizon_days':30,'confidence_level':0.5,'forecast':points}
