
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class FXResponse(BaseModel):
    base: Literal["USD"] = "USD"
    quote: Literal["PEN"] = "PEN"

    rate: Decimal = Field(gt=0)

    date: date

    source: str = Field(min_length=1)

    is_fallback: bool

    is_stale: bool
