from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    id: str
    path: str
    cite_url: str
    heading_path: list[str]
    lang: str
    text: str
    score: float
    dense_rank: int | None
    lexical_rank: int | None
