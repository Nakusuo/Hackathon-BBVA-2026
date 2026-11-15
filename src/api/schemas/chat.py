from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=500)
    conversation_id: str | None = None


class Fuente(BaseModel):
    id: str
    title: str
    page: int | str | None = None
    url: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    verified: bool = False
    sources: list[Fuente] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    intent: str | None = None
