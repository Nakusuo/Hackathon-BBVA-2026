
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class OnboardingAnswers(BaseModel):
    monthly_income: Decimal = Field(ge=0)
    monthly_expenses: Decimal = Field(ge=0)
    current_savings: Decimal = Field(ge=0)
    monthly_debt_payment: Decimal = Field(ge=0)
    income_stability: Literal[
        "stable",
        "variable",
        "irregular"
    ]


class OnboardingRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    answers: OnboardingAnswers


class OnboardingProfile(BaseModel):
    segment: str = Field(min_length=1)
    quadrant: str | None = None


class OnboardingResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    profile: OnboardingProfile
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1
    )
    model: str = Field(min_length=1)
    is_estimate: bool = True
