
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: Literal["PEN"] = "PEN"
    category: str = Field(min_length=1)
    description: str | None = None
    date: date


class ExpenseCreateResponse(BaseModel):
    id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    currency: Literal["PEN"] = "PEN"
    category: str = Field(min_length=1)
    description: str | None = None
    date: date
    created_at: datetime
