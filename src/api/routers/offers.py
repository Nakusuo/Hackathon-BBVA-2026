from fastapi import APIRouter,Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.database import get_db
from src.api.db_context import customer_scope
from src.api.schemas.offers import OffersResponse
router=APIRouter(prefix="/api/v1/customers",tags=["Financial Offers"])
@router.get("/{customer_id}/offers",response_model=OffersResponse)
def get_financial_offers(customer_id:str,db:Session=Depends(get_db)):
    customer_scope(db,customer_id)
    # No hay catálogo de ofertas reales en la BD. No se fabrican productos financieros.
    return {"customer_id":customer_id,"currency":"PEN","offers":[]}
