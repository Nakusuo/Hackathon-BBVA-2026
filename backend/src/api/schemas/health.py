
from typing import Literal

from pydantic import BaseModel, Field


class FinancialHealthResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    status: str
    quadrant: Literal["Q1", "Q2", "Q3", "Q4"]
    emergency_fund_months: float = Field(ge=0)
    currency: Literal["PEN"] = "PEN"
