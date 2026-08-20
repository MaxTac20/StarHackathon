from collections.abc import AsyncIterator, Sequence
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest
from app.schemas.retrieval import RetrievedChunk
from app.services.chat import (
    CitationIntegrityError,
    GroundedChatAnswerer,
    contextual_retrieval_query,
)
from app.services.embeddings import ChatStreamEvent, ChatUsage, EmbeddingBatch
from app.services.retrieval import RetrievalRun


def request_with_turns(*turns: tuple[str, str]) -> ChatRequest:
    return ChatRequest.model_validate(
        {
            "id": "conversation-test",
            "messages": [
                {
                    "role": role,
                    "parts": [{"type": "text", "text": text}],
                }
                for role, text in turns
            ],
        }
    )


def retrieved_chunk(
    *,
    chunk_id: str = "paas/details/envs#add-envs:0",
    path: str = "paas/details/envs",
    cite_url: str = "https://docs.liara.ir/paas/details/envs/#add-envs",
    text: str = "متغیرها را با دستور liara env:set تنظیم کنید.",
) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        path=path,
        cite_url=cite_url,
        heading_path=["متغیرهای محیطی", "اضافه‌کردن متغیر"],
        lang="fa",
        text=text,
        score=0.02,
        dense_rank=1,
        lexical_rank=1,
    )


def retrieval_run(results: list[RetrievedChunk]) -> RetrievalRun:
    return RetrievalRun(
        query_variants=[],
        results=results,
        embedding_tokens=7,
        embedding_latency_seconds=0.01,
    )


class FakeProvider:
    def __init__(self, events: list[ChatStreamEvent] | None = None) -> None:
        self.events = events or []
        self.chat_calls: list[dict[str, object]] = []

    async def embed_texts(self, texts: list[str]) -> EmbeddingBatch:
        raise AssertionError(f"retrieval was mocked, embedding should not run: {texts}")

    async def stream_chat(
        self,
        *,
        system_prompt: str,
        messages: Sequence[dict[str, object]],
        model: str = "openai/gpt-5.6-luna",
        reasoning_effort: str = "high",
        max_tokens: int = 3000,
    ) -> AsyncIterator[ChatStreamEvent]:
        self.chat_calls.append(
            {
                "system_prompt": system_prompt,
                "messages": messages,
                "model": model,
                "reasoning_effort": reasoning_effort,
                "max_tokens": max_tokens,
            }
        )
        for event in self.events:
            yield event

    async def aclose(self) -> None:
        raise AssertionError("injected providers are not owned by the answerer")


async def collect(answerer: GroundedChatAnswerer, request: ChatRequest) -> list[dict[str, object]]:
    return [event async for event in answerer.stream(request)]


async def test_empty_retrieval_refuses_without_calling_the_model() -> None:
    provider = FakeProvider()

    async def empty_retriever(*args, **kwargs) -> RetrievalRun:  # type: ignore[no-untyped-def]
        return retrieval_run([])

    answerer = GroundedChatAnswerer(
        cast(AsyncSession, object()),
        provider=provider,
        retriever=empty_retriever,
    )
    events = await collect(
        answerer, request_with_turns(("user", "آیا لیارا روی ماه دیتاسنتر دارد؟"))
    )

    assert provider.chat_calls == []
    sources = next(event["data"] for event in events if event["type"] == "data-sources")
    answer = "".join(cast(str, event["delta"]) for event in events if event["type"] == "text-delta")
    assert sources == []
    assert "پاسخ قابل اتکایی" in answer
    assert any(event["type"] == "data-notice" for event in events)


async def test_only_retrieved_source_ids_can_materialize_citation_urls() -> None:
    provider = FakeProvider(
        [
            ChatStreamEvent(kind="reasoning", text="Using the retrieved environment page."),
            ChatStreamEvent(
                kind="content",
                text="Set the variable with `liara env:set`. [[S1]]\n",
            ),
            ChatStreamEvent(
                kind="usage",
                usage=ChatUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30),
            ),
        ]
    )

    async def one_result(*args, **kwargs) -> RetrievalRun:  # type: ignore[no-untyped-def]
        return retrieval_run([retrieved_chunk()])

    answerer = GroundedChatAnswerer(
        cast(AsyncSession, object()),
        provider=provider,
        retriever=one_result,
    )
    events = await collect(answerer, request_with_turns(("user", "How do I set an env var?")))
    answer = "".join(cast(str, event["delta"]) for event in events if event["type"] == "text-delta")

    assert "[1](https://docs.liara.ir/paas/details/envs/#add-envs)" in answer
    assert provider.chat_calls[0]["reasoning_effort"] == "high"
    messages = cast(list[dict[str, str]], provider.chat_calls[0]["messages"])
    assert '<SOURCE id="S1"' in messages[-1]["content"]
    assert "https://docs.liara.ir/" not in messages[-1]["content"]


async def test_unretrieved_source_id_is_rejected_before_it_becomes_a_link() -> None:
    provider = FakeProvider(
        [
            ChatStreamEvent(
                kind="content",
                text="Set the value this way. [[S99]]\n",
            )
        ]
    )

    async def one_result(*args, **kwargs) -> RetrievalRun:  # type: ignore[no-untyped-def]
        return retrieval_run([retrieved_chunk()])

    answerer = GroundedChatAnswerer(
        cast(AsyncSession, object()),
        provider=provider,
        retriever=one_result,
    )

    with pytest.raises(CitationIntegrityError):
        await collect(answerer, request_with_turns(("user", "How do I set an env var?")))


async def test_model_no_grounding_sentinel_becomes_a_practical_refusal() -> None:
    provider = FakeProvider([ChatStreamEvent(kind="content", text="[[NO_GROUNDING]]")])

    async def one_result(*args, **kwargs) -> RetrievalRun:  # type: ignore[no-untyped-def]
        return retrieval_run([retrieved_chunk(text="An unrelated section.")])

    answerer = GroundedChatAnswerer(
        cast(AsyncSession, object()),
        provider=provider,
        retriever=one_result,
    )
    events = await collect(
        answerer,
        request_with_turns(("user", "Does Liara operate a lunar datacenter?")),
    )
    answer = "".join(cast(str, event["delta"]) for event in events if event["type"] == "text-delta")

    assert "could not find a reliable answer" in answer
    assert "[[NO_GROUNDING]]" not in answer


def test_follow_up_query_restates_the_prior_subject_for_retrieval() -> None:
    request = request_with_turns(
        ("user", "چطور PostgreSQL را به برنامه Node.js وصل کنم؟"),
        ("assistant", "پاسخ قبلی"),
        ("user", "و برای جنگو؟"),
    )

    query = contextual_retrieval_query(request)

    assert "PostgreSQL" in query
    assert "Node.js" not in query
    assert "جنگو" in query
    assert "و برای جنگو؟" in query


async def test_verified_defective_page_is_marked_and_disclosed() -> None:
    provider = FakeProvider([ChatStreamEvent(kind="content", text="[[NO_GROUNDING]]")])
    defective = retrieved_chunk(
        chunk_id="dbaas/redis/how-tos/connect-via-platform/dotnet#page:0",
        path="dbaas/redis/how-tos/connect-via-platform/dotnet",
        cite_url="https://docs.liara.ir/dbaas/redis/how-tos/connect-via-platform/dotnet/",
        text="اتصال Redis در Flask با pip install redis",
    )

    async def defective_result(*args, **kwargs) -> RetrievalRun:  # type: ignore[no-untyped-def]
        return retrieval_run([defective])

    answerer = GroundedChatAnswerer(
        cast(AsyncSession, object()),
        provider=provider,
        retriever=defective_result,
    )
    events = await collect(
        answerer,
        request_with_turns(("user", "How do I connect to Redis from .NET?")),
    )
    sources = next(event["data"] for event in events if event["type"] == "data-sources")
    notices = [event["data"] for event in events if event["type"] == "data-notice"]

    assert cast(list[dict[str, str]], sources)[0]["title"].startswith("⚠")
    assert any("Flask and Python" in cast(dict[str, str], notice)["text"] for notice in notices)
