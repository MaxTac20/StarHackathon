"""Add hybrid-retrieval document chunks.

Revision ID: 20260820_0002
Revises: 20260819_0001

Qwen3-Embedding-8B emits 4096 dimensions natively, but pgvector's HNSW
index supports at most 2000 dimensions for ``vector``. The application
therefore requests the model's Matryoshka output at 1024 dimensions.
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260820_0002"
down_revision: str | Sequence[str] | None = "20260819_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=512), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("anchor", sa.String(length=512), nullable=True),
        sa.Column("cite_url", sa.Text(), nullable=False),
        sa.Column("heading_path", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("lang", sa.String(length=16), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_norm", sa.Text(), nullable=False),
        sa.Column("code_blocks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("commit", sa.String(length=64), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(dim=1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_text_norm_fts "
        "ON document_chunks USING gin (to_tsvector('simple', text_norm))"
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding SET STORAGE PLAIN")


def downgrade() -> None:
    op.drop_table("document_chunks")
