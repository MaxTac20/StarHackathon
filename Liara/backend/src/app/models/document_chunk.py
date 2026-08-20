from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String, Text, func, literal_column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIMENSIONS = 1024


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(512), primary_key=True)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    anchor: Mapped[str | None] = mapped_column(String(512))
    cite_url: Mapped[str] = mapped_column(Text, nullable=False)
    heading_path: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    lang: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_norm: Mapped[str] = mapped_column(Text, nullable=False)
    code_blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    source_commit: Mapped[str] = mapped_column("commit", String(64), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))

    __table_args__ = (
        Index(
            "ix_document_chunks_text_norm_fts",
            func.to_tsvector(literal_column("'simple'"), text_norm),
            postgresql_using="gin",
        ),
        Index(
            "ix_document_chunks_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
