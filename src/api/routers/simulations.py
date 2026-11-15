from datetime import date,timedelta
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.financial_data import financial_snapshot,balance_projection
from src.api.schemas.simulations import SimulationRequest,SimulationResponse
router=APIRouter(prefix='/api/v1',tags=['Simulations'])

@router.post('/simulations',response_model=SimulationResponse)
def create_simulation(request:SimulationRequest,db:Session=Depends(get_db)):
    s=financial_snapshot(db,request.customer_id)
    baseline=balance_projection(s,request.horizon_days)
    simulated=[]
    for day,v in enumerate(baseline,1):
        adjustment=0
        for change in request.changes:
            sign=1 if change.type=='income' else -1
            occurrences=1 if change.frequency=='once' else 1+(day-1)//30
            adjustment+=sign*change.amount*occurrences
        simulated.append(round(v+adjustment,2))
    def scenario(values):
        return {'final_balance':values[-1],'negative_balance_days':sum(v<0 for v in values),
                'forecast':[{'date':date.today()+timedelta(days=i+1),'predicted_balance':v} for i,v in enumerate(values)]}
    return {'customer_id':request.customer_id,'currency':'PEN','horizon_days':request.horizon_days,
        'baseline':scenario(baseline),'simulated':scenario(simulated),'difference':round(simulated[-1]-baseline[-1],2),
        'disclaimer':'Proyección lineal orientativa basada en datos registrados; no es predicción garantizada ni asesoría financiera.'}
