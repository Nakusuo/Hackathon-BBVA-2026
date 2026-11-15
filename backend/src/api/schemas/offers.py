
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class FinancialOffer(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    estimated_benefit: Decimal = Field(ge=0)
    eligible: bool
    disclaimer: str = Field(min_length=1)


class OffersResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    currency: Literal["PEN"] = "PEN"
    offers: list[FinancialOffer] = Field(
        default_factory=list,
        max_length=3
    )
