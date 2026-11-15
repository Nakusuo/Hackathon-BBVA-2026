from fastapi import APIRouter,HTTPException
from src.api.schemas.fx import FXResponse
router=APIRouter(prefix='/api/v1',tags=['Exchange Rate'])

@router.get('/fx',response_model=FXResponse)
def get_exchange_rate(base:str='USD',quote:str='PEN'):
    if base!='USD' or quote!='PEN': raise HTTPException(status_code=422,detail='Solo USD/PEN en MVP')
    raise HTTPException(status_code=503,detail='No se configuró un proveedor verificable de tipo de cambio USD/PEN')
