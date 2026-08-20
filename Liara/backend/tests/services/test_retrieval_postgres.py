import json
import os

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models.document_chunk import EMBEDDING_DIMENSIONS, DocumentChunk
from app.services.corpus import embed_unembedded_chunks
from app.services.embeddings import EMBEDDING_MODEL, OpenRouterEmbeddingClient
from app.services.retrieval import dense_search, lexical_search
from app.utils.persian import ZWNJ, query_variants

DATABASE_URL = os.getenv("RETRIEVAL_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    DATABASE_URL is None,
    reason="set RETRIEVAL_TEST_DATABASE_URL to run pgvector integration tests",
)


def _unit_vector(index: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[index] = 1.0
    return vector


async def test_postgres_lexical_fallback_and_zwnj_dense_variants() -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        await session.execute(delete(DocumentChunk))
        session.add_all(
            [
                DocumentChunk(
                    id="test:unrelated",
                    path="test/unrelated",
                    url="https://docs.liara.ir/test/unrelated/",
                    anchor=None,
                    cite_url="https://docs.liara.ir/test/unrelated/",
                    heading_path=["نامرتبط"],
                    lang="fa",
                    text="استقرار برنامه",
                    text_norm="استقرار برنامه",
                    code_blocks=[],
                    token_estimate=2,
                    source_commit="test",
                    embedding=_unit_vector(0),
                ),
                DocumentChunk(
                    id="test:backup",
                    path="test/backup",
                    url="https://docs.liara.ir/test/backup/",
                    anchor=None,
                    cite_url="https://docs.liara.ir/test/backup/",
                    heading_path=["پشتیبان‌گیری"],
                    lang="fa",
                    text="روش پشتیبان‌گیری از PostgreSQL",
                    text_norm="روش پشتیبانگیری از PostgreSQL",
                    code_blocks=[],
                    token_estimate=4,
                    source_commit="test",
                    embedding=_unit_vector(1),
                ),
                DocumentChunk(
                    id="test:zwnj",
                    path="test/zwnj",
                    url="https://docs.liara.ir/test/zwnj/",
                    anchor=None,
                    cite_url="https://docs.liara.ir/test/zwnj/",
                    heading_path=["اضافه‌کردن"],
                    lang="fa",
                    text="اضافه‌کردن متغیر",
                    text_norm="اضافهکردن متغیر",
                    code_blocks=[],
                    token_estimate=3,
                    source_commit="test",
                    embedding=_unit_vector(2),
                ),
                DocumentChunk(
                    id="test:pending-embedding",
                    path="test/pending-embedding",
                    url="https://docs.liara.ir/test/pending-embedding/",
                    anchor=None,
                    cite_url="https://docs.liara.ir/test/pending-embedding/",
                    heading_path=["در انتظار بردار"],
                    lang="fa",
                    text="متن آزمایشی",
                    text_norm="متن آزمایشی",
                    code_blocks=[],
                    token_estimate=2,
                    source_commit="test",
                    embedding=None,
                ),
            ]
        )
        await session.flush()

        dense = await dense_search(session, [_unit_vector(0)], limit=1)
        lexical = await lexical_search(
            session,
            query_variants(f"پشتیبان{ZWNJ}گیری"),
            limit=5,
        )
        assert [chunk.id for chunk in dense] == ["test:unrelated"]
        assert "test:backup" in {chunk.id for chunk in lexical}

        variants = query_variants(f"اضافه{ZWNJ}کردن")
        assert len(variants) == 2
        variant_dense = await dense_search(
            session,
            [_unit_vector(1), _unit_vector(2)],
            limit=1,
        )
        assert {chunk.id for chunk in variant_dense} == {"test:backup", "test:zwnj"}

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            inputs = payload["input"]
            assert isinstance(inputs, list)
            assert len(inputs) == 1
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "embedding": _unit_vector(3),
                            "index": 0,
                            "object": "embedding",
                        }
                    ],
                    "model": EMBEDDING_MODEL,
                    "object": "list",
                    "usage": {"prompt_tokens": 2, "total_tokens": 2},
                },
            )

        http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        embedding_client = OpenRouterEmbeddingClient(
            SecretStr("test-key"),
            http_client=http_client,
        )
        embedding_stats = await embed_unembedded_chunks(session, embedding_client)
        persisted_embedding = await session.scalar(
            select(DocumentChunk.embedding).where(DocumentChunk.id == "test:pending-embedding")
        )
        second_run = await embed_unembedded_chunks(session, embedding_client)
        await http_client.aclose()

        assert embedding_stats.chunks == 1
        assert persisted_embedding is not None
        assert second_run.chunks == 0
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()
