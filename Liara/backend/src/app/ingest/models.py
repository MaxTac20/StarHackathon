from typing import Literal

from pydantic import BaseModel, ConfigDict


class CodeBlockRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lang: str
    source: Literal["fence", "cast"]
    text: str


class CorpusRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    path: str
    url: str
    anchor: str | None
    cite_url: str
    heading_path: list[str]
    lang: Literal["fa"]
    text: str
    text_norm: str
    code_blocks: list[CodeBlockRecord]
    token_estimate: int
    commit: str


class ManifestKey(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    frequency: int
    example_pages: list[str]


class ManifestInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commit: str
    keys: list[ManifestKey]
