from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    # Con el mismo id, reenviar el gasto no lo duplica.
    id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,40}$")
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
    # La descripción libre puede traer datos personales: se recibe pero no se guarda ni se devuelve.
    description: None = None
    date: date
    created_at: datetime
    duplicate: bool = False
