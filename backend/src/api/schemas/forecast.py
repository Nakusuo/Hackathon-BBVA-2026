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
    first_risk_date: date | None = None
    model: str | None = None
    data_as_of: date | None = None
    risk_probability: float | None = Field(default=None, ge=0, le=1)
    synthetic_data: bool = True
    sample_only: bool = False
