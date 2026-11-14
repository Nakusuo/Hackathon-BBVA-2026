
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "income",
    "gratification",
    "cts",
    "recurring_expense",
    "negative_balance_risk",
]

EventPriority = Literal["low", "medium", "high"]


class FinancialEvent(BaseModel):
    id: str = Field(min_length=1)
    type: EventType
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    event_date: date
    priority: EventPriority
    estimated_impact: float
    notified: bool = False


class EventsResponse(BaseModel):
    customer_id: str = Field(min_length=1)
    events: list[FinancialEvent]
    weekly_notifications_remaining: int = Field(
        ge=0,
        le=3,
    )
