from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    parts: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    id: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    trigger: Literal["submit-message", "regenerate-message"] | None = None
    message_id: str | None = Field(default=None, alias="messageId")
