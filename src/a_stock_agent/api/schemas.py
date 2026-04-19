from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_id: str | None = None
    message: str
    symbols: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    data_timestamp: str | None
    disclaimer: str


class KnowledgeImportRequest(BaseModel):
    file_path: str
    force: bool = False
