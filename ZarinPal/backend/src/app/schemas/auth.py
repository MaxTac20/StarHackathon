from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=512)


class MerchantSelectionRequest(BaseModel):
    merchant_key: str = Field(min_length=1, max_length=128)


class MerchantCategorySummary(BaseModel):
    category_id: str
    title_fa: str


class SelectedMerchant(BaseModel):
    merchant_key: str
    categories: list[MerchantCategorySummary]


class SessionResponse(BaseModel):
    authenticated: bool
    selected_merchant: SelectedMerchant | None = None
