"""RAG document schemas."""

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    chunk_count: int
    upload_time: str


class DocumentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, examples=["What are the key findings?"])
    document_id: int | None = Field(default=None, description="Specific document; omit for all user docs")
    top_k: int = Field(default=4, ge=1, le=20)


class DocumentAskResponse(BaseModel):
    answer: str
    sources: list[str]
