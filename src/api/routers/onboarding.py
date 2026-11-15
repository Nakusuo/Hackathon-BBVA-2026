from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.db_context import customer_scope
from src.api.schemas.onboarding import OnboardingRequest, OnboardingResponse
router=APIRouter(prefix='/api/v1',tags=['Onboarding'])

@router.post('/onboarding',response_model=OnboardingResponse)
def create_onboarding(request:OnboardingRequest,db:Session=Depends(get_db)):
    customer_scope(db,request.customer_id)
    a=request.answers
    db.execute(text("""INSERT INTO app.onboarding_financiero
      (customer_id,monthly_income,monthly_expenses,current_savings,monthly_debt_payment,income_stability)
      VALUES (:cid,:income,:expenses,:savings,:debt,:stability)
      ON CONFLICT(customer_id) DO UPDATE SET monthly_income=EXCLUDED.monthly_income,
      monthly_expenses=EXCLUDED.monthly_expenses,current_savings=EXCLUDED.current_savings,
      monthly_debt_payment=EXCLUDED.monthly_debt_payment,income_stability=EXCLUDED.income_stability,
      actualizado_en=now()"""),{'cid':request.customer_id,'income':a.monthly_income,'expenses':a.monthly_expenses,'savings':a.current_savings,'debt':a.monthly_debt_payment,'stability':a.income_stability})
    db.commit()
    return {'customer_id':request.customer_id,'profile':None,'confidence':None,'model':'stored_answers_no_classifier','is_estimate':True}
