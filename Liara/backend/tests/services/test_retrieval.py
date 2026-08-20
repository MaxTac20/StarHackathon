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


def test_rrf_beats_both_legs_on_adversarial_top_three() -> None:
    relevant = {"relevant-a", "relevant-b", "relevant-c"}
    dense = [
        _chunk("dense-noise", 0.1),
        _chunk("relevant-a", 0.2),
        _chunk("relevant-b", 0.3),
        _chunk("relevant-c", 0.4),
        *[_chunk(f"dense-tail-{index}", 0.5 + index) for index in range(4)],
    ]
    lexical = [
        _chunk("lexical-noise", 1.0),
        _chunk("relevant-c", 0.9),
        _chunk("relevant-b", 0.8),
        _chunk("relevant-a", 0.7),
        *[_chunk(f"lexical-tail-{index}", 0.6 - index / 10) for index in range(4)],
    ]

    fused = reciprocal_rank_fusion(dense, lexical, top_k=3)
    dense_relevant = sum(chunk.id in relevant for chunk in dense[:3])
    lexical_relevant = sum(chunk.id in relevant for chunk in lexical[:3])
    fused_relevant = sum(chunk.id in relevant for chunk in fused)

    assert [chunk.id for chunk in dense[:3]] != [chunk.id for chunk in lexical[:3]]
    assert [chunk.id for chunk in fused] == ["relevant-a", "relevant-b", "relevant-c"]
    assert fused_relevant > dense_relevant
    assert fused_relevant > lexical_relevant


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
        query_text: str,
        *,
        limit: int,
    ) -> list[RankedChunk]:
        assert query_text == "پشتیبانگیری"
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


async def test_query_uses_both_zwnj_variants_for_dense_but_only_stripped_for_lexical(
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
        query_text: str,
        *,
        limit: int,
    ) -> list[RankedChunk]:
        assert query_text == expected_variants[0]
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


def test_lexical_query_filters_persian_function_words() -> None:
    query = "چطور متغیرهای محیطی را از لیارا اضافهکنم؟"

    assert retrieval_service._or_query_terms(query) == ("متغیرهای OR محیطی OR لیارا OR اضافهکنم؟")


def test_lexical_query_filters_english_function_words() -> None:
    # The product is bilingual, so an English question needs filtering too.
    # Unfiltered, this searches for "how OR do OR I OR a", which on the real
    # corpus buries the Django pages under unrelated AI cookbook pages.
    assert retrieval_service._or_query_terms("how do I deploy a Django app") == (
        "deploy OR Django OR app"
    )


def test_platform_names_that_are_also_english_words_stay_searchable() -> None:
    # "go" and "next" name Liara platforms. Generic stopword lists drop them,
    # which would make those platforms unsearchable by name.
    assert retrieval_service._or_query_terms("go version") == "go OR version"
    assert "Next.js" in retrieval_service._or_query_terms("how to use Next.js")


def test_lexical_statement_uses_simple_configuration() -> None:
    statement = retrieval_service._lexical_statement(
        "چطور متغیرهای محیطی را اضافهکنم؟",
        limit=10,
    )
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),  # type: ignore[no-untyped-call]
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "to_tsvector('simple', document_chunks.text_norm)" in sql
    assert "websearch_to_tsquery('simple', 'متغیرهای OR محیطی OR اضافهکنم؟')" in sql
    assert "چطور" not in sql
    assert " را " not in sql
    assert "'arabic'" not in sql
