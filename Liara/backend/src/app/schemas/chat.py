from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    parts: list[dict[str, Any]] = Field(default_factory=list)


class ProfileChip(BaseModel):
    """One fact the conversation has established about the user's setup.

    Session-scoped and client-held: there are no accounts, so this arrives with
    each request rather than being looked up. See ``docs/STATE.md``.
    """

    kind: Literal["platform", "service", "region", "other"]
    value: str = Field(min_length=1, max_length=40)


class ChatRequest(BaseModel):
    id: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    profile: list[ProfileChip] = Field(default_factory=list, max_length=8)
    trigger: Literal["submit-message", "regenerate-message"] | None = None
    message_id: str | None = Field(default=None, alias="messageId")
