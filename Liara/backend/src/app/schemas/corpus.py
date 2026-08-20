from typing import Literal

from pydantic import BaseModel


class CodeBlock(BaseModel):
    lang: str
    source: Literal["fence", "cast"]
    text: str


class CorpusRecord(BaseModel):
    id: str
    path: str
    url: str
    anchor: str | None
    cite_url: str
    heading_path: list[str]
    lang: str
    text: str
    text_norm: str
    code_blocks: list[CodeBlock]
    token_estimate: int
    commit: str
