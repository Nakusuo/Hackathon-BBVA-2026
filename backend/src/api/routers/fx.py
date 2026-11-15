from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.fx import FXResponse
from src.bcrp.servicio import SerieNoDisponible, ServicioBCRP, fx_contrato

router = APIRouter(
    prefix="/api/v1",
    tags=["Exchange Rate"]
)


def obtener_servicio() -> ServicioBCRP:
    return ServicioBCRP()


@router.get(
    "/fx",
    response_model=FXResponse
)
def get_exchange_rate(
    base: str = "USD",
    quote: str = "PEN",
    servicio: ServicioBCRP = Depends(obtener_servicio)
):
    if base != "USD" or quote != "PEN":
        raise HTTPException(
            status_code=422,
            detail="Solo se admite USD/PEN en el MVP"
        )

    try:
        return fx_contrato(servicio.obtener("tipo_cambio"))
    except SerieNoDisponible:
        raise HTTPException(
            status_code=503,
            detail="Tipo de cambio no disponible"
        ) from None
