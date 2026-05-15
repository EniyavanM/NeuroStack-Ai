"""Chat schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000, examples=["Explain multi-agent AI systems"])
    conversation_id: int | None = Field(default=None, description="Existing conversation ID")
    stream: bool = Field(default=False, description="Enable SSE streaming")
    use_agents: bool = Field(default=False, description="Route through multi-agent orchestrator")


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: str
    messages: list[MessageOut] = []


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    agent_used: str | None = None
