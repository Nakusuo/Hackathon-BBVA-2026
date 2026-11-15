
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SimulationChange(BaseModel):
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    frequency: Literal["once", "monthly"]
    description: str = Field(min_length=1)


class SimulationRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    horizon_days: int = Field(default=30, gt=0)
    changes: list[SimulationChange]


class SimulationForecastPoint(BaseModel):
    date: date
    predicted_balance: float


class SimulationScenario(BaseModel):
    final_balance: float
    negative_balance_days: int = Field(ge=0)
    forecast: list[SimulationForecastPoint]


class SimulationResponse(BaseModel):
    customer_id: str
    currency: Literal["PEN"] = "PEN"
    horizon_days: int
    baseline: SimulationScenario
    simulated: SimulationScenario
    difference: float
    disclaimer: str
