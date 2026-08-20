from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.auth import MerchantCategorySummary


class MerchantSort(StrEnum):
    merchant_key = "merchant_key"
    session_count = "session_count"
    attempt_count = "attempt_count"
    terminal_count = "terminal_count"
    latest_activity = "latest_activity"


class SortDirection(StrEnum):
    asc = "asc"
    desc = "desc"


class MerchantSummary(BaseModel):
    merchant_key: str
    categories: list[MerchantCategorySummary]
    session_count: int
    attempt_count: int
    terminal_count: int
    first_session_at: datetime | None
    latest_session_at: datetime | None


class MerchantListResponse(BaseModel):
    items: list[MerchantSummary]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
