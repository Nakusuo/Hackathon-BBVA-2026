
from typing import Any, Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    estimated_impact: float = Field(ge=0)
    impact_type: Literal[
        "expense_reduction",
        "savings_allocation"
    ]
    impact_period: str
    reason: str
    data_used: list[str] | dict[str, Any]
    assumptions: list[str]
    confidence: Literal["alta", "media", "baja"]
    disclaimer: str


class RecommendationsResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    currency: Literal["PEN"] = "PEN"
    recommendations: list[Recommendation] = Field(
        max_length=3
    )
