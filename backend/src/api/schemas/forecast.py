
from datetime import date

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    date: date
    predicted_balance: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    currency: str = "PEN"
    horizon_days: int = Field(default=30, gt=0)
    confidence_level: float = Field(default=0.80, gt=0, le=1)
    forecast: list[ForecastPoint]
