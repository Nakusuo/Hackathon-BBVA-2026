
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator



class SavingsGoal(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal | None = Field(default=None, ge=0)

    currency: Literal["PEN"] = "PEN"
    target_date: date | None = None

    progress_percentage: float | None = Field(
        default=None,
        ge=0,
        le=100
    )

    suggested_biweekly_saving: Decimal | None = None
    projected_year_end_savings: Decimal | None = None

    completion_probability: float | None = Field(
        default=None,
        ge=0,
        le=1
    )



class GoalsResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    currency: Literal["PEN"] = "PEN"
    goals: list[SavingsGoal]



class GoalCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0
    )
    currency: Literal["PEN"] = "PEN"
    target_date: date

    @model_validator(mode="after")
    def validate_initial_savings(self):
        if self.current_amount > self.target_amount:
            raise ValueError(
                "El ahorro inicial no puede superar "
                "el monto objetivo"
            )

        return self



class GoalCreateResponse(BaseModel):
    id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    name: str
    target_amount: Decimal
    current_amount: Decimal = Field(ge=0)
    currency: Literal["PEN"] = "PEN"
    target_date: date
    progress_percentage: float = Field(ge=0)
