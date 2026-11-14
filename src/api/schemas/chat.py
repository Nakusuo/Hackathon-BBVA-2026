
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    verified: bool = False
    sources: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
