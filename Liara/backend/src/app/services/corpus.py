from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import cast

from pydantic import ValidationError
from sqlalchemy import Table, bindparam, case, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.schemas.corpus import CorpusRecord
from app.services.embeddings import EmbeddingInput, OpenRouterEmbeddingClient


class CorpusLoadError(RuntimeError):
    pass


@dataclass(frozen=True)
class CorpusLoadStats:
    records: int
    batches: int


@dataclass(frozen=True)
class EmbeddingRunStats:
    chunks: int
    batches: int
    prompt_tokens: int
    total_tokens: int
    api_latency_seconds: float
    wall_seconds: float


async def load_corpus_jsonl(
    session: AsyncSession,
    corpus_path: Path,
    *,
    batch_size: int = 100,
) -> CorpusLoadStats:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    records = 0
    batches = 0
    pending: list[CorpusRecord] = []

    with corpus_path.open(encoding="utf-8") as corpus_file:
        for line_number, line in enumerate(corpus_file, start=1):
            if not line.strip():
                continue
            try:
                pending.append(CorpusRecord.model_validate_json(line))
            except ValidationError as exc:
                raise CorpusLoadError(
                    f"{corpus_path}:{line_number}: invalid corpus record"
                ) from exc

            if len(pending) == batch_size:
                await _upsert_records(session, pending)
                await session.commit()
                records += len(pending)
                batches += 1
                pending.clear()

    if pending:
        await _upsert_records(session, pending)
        await session.commit()
        records += len(pending)
        batches += 1

    return CorpusLoadStats(records=records, batches=batches)


async def _upsert_records(session: AsyncSession, records: Sequence[CorpusRecord]) -> None:
    values = [
        {
            "id": record.id,
            "path": record.path,
            "url": record.url,
            "anchor": record.anchor,
            "cite_url": record.cite_url,
            "heading_path": record.heading_path,
            "lang": record.lang,
            "text": record.text,
            "text_norm": record.text_norm,
            "code_blocks": [block.model_dump() for block in record.code_blocks],
            "token_estimate": record.token_estimate,
            "commit": record.commit,
        }
        for record in records
    ]
    statement = insert(DocumentChunk).values(values)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[DocumentChunk.id],
        set_={
            "path": excluded.path,
            "url": excluded.url,
            "anchor": excluded.anchor,
            "cite_url": excluded.cite_url,
            "heading_path": excluded.heading_path,
            "lang": excluded.lang,
            "text": excluded.text,
            "text_norm": excluded.text_norm,
            "code_blocks": excluded.code_blocks,
            "token_estimate": excluded.token_estimate,
            "commit": excluded.commit,
            "embedding": case(
                (
                    or_(
                        DocumentChunk.text != excluded.text,
                        DocumentChunk.heading_path != excluded.heading_path,
                    ),
                    None,
                ),
                else_=DocumentChunk.embedding,
            ),
        },
    )
    await session.execute(statement)


async def embed_unembedded_chunks(
    session: AsyncSession,
    embedding_client: OpenRouterEmbeddingClient,
) -> EmbeddingRunStats:
    started_at = monotonic()
    rows = (
        await session.execute(
            select(
                DocumentChunk.id,
                DocumentChunk.heading_path,
                DocumentChunk.text,
            )
            .where(DocumentChunk.embedding.is_(None))
            .order_by(DocumentChunk.id)
        )
    ).all()
    inputs = [
        EmbeddingInput(
            key=chunk_id,
            text=_embedding_text(heading_path=heading_path, text=text),
        )
        for chunk_id, heading_path, text in rows
    ]

    chunks = 0
    batches = 0
    prompt_tokens = 0
    total_tokens = 0
    api_latency_seconds = 0.0

    chunks_table = cast(Table, DocumentChunk.__table__)
    statement = (
        update(chunks_table)
        .where(chunks_table.c.id == bindparam("chunk_id"))
        .values(embedding=bindparam("chunk_embedding"))
    )
    async for batch in embedding_client.iter_embeddings(inputs):
        await session.execute(
            statement,
            [{"chunk_id": item.key, "chunk_embedding": item.embedding} for item in batch.items],
        )
        await session.commit()
        chunks += len(batch.items)
        batches += 1
        prompt_tokens += batch.prompt_tokens
        total_tokens += batch.total_tokens
        api_latency_seconds += batch.latency_seconds

    return EmbeddingRunStats(
        chunks=chunks,
        batches=batches,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        api_latency_seconds=api_latency_seconds,
        wall_seconds=monotonic() - started_at,
    )


def _embedding_text(*, heading_path: Sequence[str], text: str) -> str:
    return "\n".join([*heading_path, text])
