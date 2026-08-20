import json
from typing import cast

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.retrieval as retrieval_service
from app.models.document_chunk import EMBEDDING_DIMENSIONS
from app.services.embeddings import EMBEDDING_MODEL, OpenRouterEmbeddingClient
from app.services.retrieval import RankedChunk, reciprocal_rank_fusion, retrieve
from app.utils.persian import ZWNJ


def _chunk(chunk_id: str, score: float) -> RankedChunk:
    return RankedChunk(
        id=chunk_id,
        path=f"path/{chunk_id}",
        cite_url=f"https://docs.liara.ir/{chunk_id}/",
        heading_path=[chunk_id],
        lang="fa",
        text=chunk_id,
        leg_score=score,
    )


def _embedding_handler(captured_inputs: list[str]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        inputs = payload["input"]
        assert isinstance(inputs, list)
        captured_inputs.extend(cast(list[str], inputs))
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "embedding": [float(index + 1)] * EMBEDDING_DIMENSIONS,
                        "index": index,
                        "object": "embedding",
                    }
                    for index in range(len(inputs))
                ],
                "model": EMBEDDING_MODEL,
                "object": "list",
                "usage": {"prompt_tokens": len(inputs), "total_tokens": len(inputs)},
            },
        )

    return httpx.MockTransport(handler)


def test_rrf_can_promote_consensus_above_either_legs_winner() -> None:
    dense = [_chunk("dense-winner", 0.1), _chunk("consensus", 0.2)]
    lexical = [_chunk("lexical-winner", 1.0), _chunk("consensus", 0.8)]

    fused = reciprocal_rank_fusion(dense, lexical, top_k=3)

    assert fused[0].id == "consensus"
    assert fused[0].id != dense[0].id
    assert fused[0].id != lexical[0].id


async def test_lexical_leg_recovers_a_persian_match_dense_misses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_dense(
        session: AsyncSession,
        query_embeddings: list[list[float]],
        *,
        limit: int,
    ) -> list[RankedChunk]:
        assert query_embeddings
        assert limit == 50
        return [_chunk("unrelated-dense", 0.1)]

    async def fake_lexical(
        session: AsyncSession,
        variants: list[str],
        *,
        limit: int,
    ) -> list[RankedChunk]:
        assert "پشتیبانگیری" in variants
        assert limit == 50
        return [_chunk("postgres-backup", 1.0)]

    monkeypatch.setattr(retrieval_service, "dense_search", fake_dense)
    monkeypatch.setattr(retrieval_service, "lexical_search", fake_lexical)
    captured_inputs: list[str] = []
    http_client = httpx.AsyncClient(transport=_embedding_handler(captured_inputs))
    embedding_client = OpenRouterEmbeddingClient(
        SecretStr("test-key"),
        http_client=http_client,
    )

    run = await retrieve(
        cast(AsyncSession, object()),
        embedding_client,
        f"پشتیبان{ZWNJ}گیری",
    )
    await http_client.aclose()

    lexical_result = next(result for result in run.results if result.id == "postgres-backup")
    assert lexical_result.dense_rank is None
    assert lexical_result.lexical_rank == 1


async def test_query_tries_both_zwnj_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_variants = ["اضافهکردن متغیر", f"اضافه{ZWNJ}کردن متغیر"]

    async def fake_dense(
        session: AsyncSession,
        query_embeddings: list[list[float]],
        *,
        limit: int,
    ) -> list[RankedChunk]:
        assert len(query_embeddings) == 2
        return [_chunk("joined-match", 0.1), _chunk("zwnj-match", 0.2)]

    async def fake_lexical(
        session: AsyncSession,
        variants: list[str],
        *,
        limit: int,
    ) -> list[RankedChunk]:
        assert variants == expected_variants
        return []

    monkeypatch.setattr(retrieval_service, "dense_search", fake_dense)
    monkeypatch.setattr(retrieval_service, "lexical_search", fake_lexical)
    captured_inputs: list[str] = []
    http_client = httpx.AsyncClient(transport=_embedding_handler(captured_inputs))
    embedding_client = OpenRouterEmbeddingClient(
        SecretStr("test-key"),
        http_client=http_client,
    )

    run = await retrieve(
        cast(AsyncSession, object()),
        embedding_client,
        f"اضافه{ZWNJ}کردن متغیر",
    )
    await http_client.aclose()

    assert captured_inputs == expected_variants
    assert {result.id for result in run.results} == {"joined-match", "zwnj-match"}


def test_lexical_statement_uses_simple_configuration() -> None:
    statement = retrieval_service._lexical_statement("لیارا", limit=10)
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),  # type: ignore[no-untyped-call]
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "to_tsvector('simple', document_chunks.text_norm)" in sql
    assert "websearch_to_tsquery('simple', 'لیارا')" in sql
    assert "'arabic'" not in sql
