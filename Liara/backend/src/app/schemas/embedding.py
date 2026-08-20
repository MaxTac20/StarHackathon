from pydantic import BaseModel, Field


class EmbeddingDatum(BaseModel):
    embedding: list[float]
    index: int
    object: str


class EmbeddingUsage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    data: list[EmbeddingDatum]
    model: str
    object: str
    usage: EmbeddingUsage = Field(default_factory=EmbeddingUsage)
