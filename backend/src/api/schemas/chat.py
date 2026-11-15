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


class PropuestaMeta(BaseModel):
    """Meta que el chat ofrece guardar. La app la crea solo si la persona acepta."""

    name: str = Field(min_length=1, max_length=40)
    target: float = Field(gt=0)
    date: str


class Opcion(BaseModel):
    """Botón de respuesta rápida: el chat envía `question` si la persona lo toca."""

    id: str
    label: str
    question: str


class ChatResponse(BaseModel):
    conversation_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    verified: bool = False
    sources: list[Fuente] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    intent: str | None = None
    goal_proposal: PropuestaMeta | None = None
    options: list[Opcion] = Field(default_factory=list)
