
from datetime import date

from fastapi import APIRouter, HTTPException

from src.api.schemas.fx import FXResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["Exchange Rate"]
)


@router.get(
    "/fx",
    response_model=FXResponse
)
def get_exchange_rate(
    base: str = "USD",
    quote: str = "PEN"
):
    if base != "USD" or quote != "PEN":
        raise HTTPException(
            status_code=422,
            detail="Solo se admite USD/PEN en el MVP"
        )

    # Valor exclusivamente sintético para MG-03.
    # No representa una cotización actual del BCRP.
    return {
        "base": "USD",
        "quote": "PEN",
        "rate": "3.75",
        "date": date(2026, 1, 1),
        "source": "synthetic_demo",
        "is_fallback": True,
        "is_stale": True
    }
