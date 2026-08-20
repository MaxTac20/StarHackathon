from collections.abc import AsyncIterator, Sequence
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest
from app.schemas.retrieval import RetrievedChunk
from app.services.chat import (
    SYSTEM_PROMPT,
    CitationLineRenderer,
    GroundedChatAnswerer,
    SourceBinding,
    answer_retrieval_queries,
    contextual_retrieval_query,
    filter_retrieval_results,
    interleave_retrieval_results,
    provider_messages,
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
    assert messages[-1]["content"].startswith("REQUIRED ANSWER LANGUAGE: English.")
    assert '<SOURCE id="S1"' in messages[-1]["content"]
    assert "https://docs.liara.ir/" not in messages[-1]["content"]


async def test_unretrieved_source_id_is_omitted_before_it_becomes_a_link() -> None:
    provider = FakeProvider(
        [
            ChatStreamEvent(
                kind="content",
                text=("Use the retrieved setting. [[S1]]\nDo something unsupported. [[S99]]\n"),
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

    events = await collect(answerer, request_with_turns(("user", "How do I set an env var?")))
    answer = "".join(cast(str, event["delta"]) for event in events if event["type"] == "text-delta")

    assert "Use the retrieved setting." in answer
    assert "unsupported" not in answer
    assert "S99" not in answer
    assert any(event["type"] == "data-notice" for event in events)


async def test_draft_with_only_unretrieved_citations_becomes_a_refusal() -> None:
    provider = FakeProvider(
        [ChatStreamEvent(kind="content", text="Do something unsupported. [[S99]]\n")]
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

    assert "could not find a reliable answer" in answer
    assert "unsupported" not in answer
    assert any(event["type"] == "data-notice" for event in events)


async def test_inline_numbers_match_the_deduplicated_source_panel() -> None:
    duplicate_url = "https://docs.liara.ir/paas/details/envs/#add-envs"
    provider = FakeProvider(
        [ChatStreamEvent(kind="content", text="Use the second chunk. [[S2]]\n")]
    )
    first = retrieved_chunk(chunk_id="env:first", cite_url=duplicate_url)
    second = retrieved_chunk(chunk_id="env:second", cite_url=duplicate_url)

    async def duplicate_results(*args, **kwargs) -> RetrievalRun:  # type: ignore[no-untyped-def]
        return retrieval_run([first, second])

    answerer = GroundedChatAnswerer(
        cast(AsyncSession, object()),
        provider=provider,
        retriever=duplicate_results,
    )
    events = await collect(answerer, request_with_turns(("user", "How do I set an env var?")))
    answer = "".join(cast(str, event["delta"]) for event in events if event["type"] == "text-delta")
    sources = next(event["data"] for event in events if event["type"] == "data-sources")

    assert len(cast(list[dict[str, str]], sources)) == 1
    assert f"[1]({duplicate_url})" in answer


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


def test_multi_intent_query_plans_bounded_existing_retrieval_calls() -> None:
    queries = answer_retrieval_queries(
        "فایل‌های آپلودی پاک می‌شوند؛ محدودیت Nginx را بالا ببرم و ماندگارشان کنم؟"
    )

    assert len(queries) == 3
    assert "ساخت دیسک" in queries[1]
    assert "client_max_body_size" in queries[2]


def test_exact_timeout_symbol_gets_a_high_precision_query_first() -> None:
    queries = answer_retrieval_queries(
        "How do I raise GUNICORN_TIMEOUT after a Django WORKER TIMEOUT?"
    )

    assert queries[0] == "Django WORKER TIMEOUT GUNICORN_TIMEOUT environment variable"
    assert len(queries) == 2


def test_multi_query_results_are_interleaved_instead_of_losing_an_intent() -> None:
    upload = retrieval_run(
        [
            retrieved_chunk(chunk_id="upload:0"),
            retrieved_chunk(chunk_id="upload:1"),
        ]
    )
    persistence = retrieval_run(
        [
            retrieved_chunk(chunk_id="disk:0"),
            retrieved_chunk(chunk_id="disk:1"),
        ]
    )

    merged = interleave_retrieval_results([upload, persistence], top_k=4)

    assert [result.id for result in merged] == [
        "upload:0",
        "disk:0",
        "upload:1",
        "disk:1",
    ]


def test_explicit_platform_and_surface_filter_remove_sibling_distractors() -> None:
    django = retrieved_chunk(
        chunk_id="paas/django/fix:0",
        path="paas/django/fix",
    )
    shared_disk = retrieved_chunk(
        chunk_id="paas/disks/route:0",
        path="paas/disks/route",
    )
    flask = retrieved_chunk(
        chunk_id="paas/flask/fix:0",
        path="paas/flask/fix",
    )
    iaas = retrieved_chunk(
        chunk_id="iaas/disks/mount:0",
        path="iaas/disks/mount",
    )
    ai_next = retrieved_chunk(
        chunk_id="ai/getting-started/nextjs:0",
        path="ai/getting-started/nextjs",
    )
    email = retrieved_chunk(
        chunk_id="email-server/details/common-errors:0",
        path="email-server/details/common-errors",
    )

    filtered = filter_retrieval_results(
        "در برنامه Django بعد از deploy فایل‌ها پاک می‌شوند",
        [django, shared_disk, flask, iaas, ai_next, email],
    )

    assert [result.id for result in filtered] == [
        "paas/django/fix:0",
        "paas/disks/route:0",
    ]
    assert (
        filter_retrieval_results(
            "در برنامه Django بعد از deploy فایل‌ها پاک می‌شوند",
            [flask, iaas, ai_next, email],
        )
        == []
    )


async def test_verified_defective_page_is_marked_and_disclosed() -> None:
    provider = FakeProvider(
        [
            ChatStreamEvent(
                kind="content",
                text="Install the Flask package for .NET. [[S1]]\n",
            )
        ]
    )
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
    answer = "".join(cast(str, event["delta"]) for event in events if event["type"] == "text-delta")

    assert cast(list[dict[str, str]], sources)[0]["title"].startswith("⚠")
    assert any("Flask and Python" in cast(dict[str, str], notice)["text"] for notice in notices)
    assert "could not find a reliable answer" in answer
    assert "Install the Flask package" not in answer
    assert defective.cite_url not in answer


def request_with_profile(question: str, *chips: tuple[str, str]) -> ChatRequest:
    return ChatRequest.model_validate(
        {
            "id": "conversation-test",
            "messages": [{"role": "user", "parts": [{"type": "text", "text": question}]}],
            "profile": [{"kind": kind, "value": value} for kind, value in chips],
        }
    )


def test_established_context_biases_retrieval_without_replacing_the_question() -> None:
    request = request_with_profile("چطور دیسک اضافه کنم؟", ("platform", "Django"))
    query = contextual_retrieval_query(request)

    # The question still has to match on its own terms; a stale chip shades the
    # ranking rather than substituting for what was asked.
    assert "چطور دیسک اضافه کنم؟" in query
    assert "Django" in query


def test_established_context_never_enters_the_cached_system_prefix() -> None:
    # The system block is the prompt-cache prefix. Varying it per request would
    # forfeit the cache read that makes a repeated question about a third cheaper.
    before = SYSTEM_PROMPT
    request = request_with_profile("how do I add a disk?", ("platform", "Django"))
    messages = provider_messages(
        request,
        latest_question="how do I add a disk?",
        bindings=[],
        is_persian=False,
    )

    assert SYSTEM_PROMPT == before
    assert "Django" not in SYSTEM_PROMPT
    assert any("Django" in str(message["content"]) for message in messages)


def test_established_context_is_marked_as_unciteable() -> None:
    # A chip must never be usable as evidence, or a wrong chip becomes a
    # fabricated claim rather than merely an unhelpful example.
    request = request_with_profile("how do I add a disk?", ("platform", "Django"))
    messages = provider_messages(
        request,
        latest_question="how do I add a disk?",
        bindings=[],
        is_persian=False,
    )
    content = str(messages[-1]["content"])

    assert "supports no claim" in content


def test_no_profile_leaves_the_prompt_untouched() -> None:
    plain = provider_messages(
        request_with_turns(("user", "how do I add a disk?")),
        latest_question="how do I add a disk?",
        bindings=[],
        is_persian=False,
    )
    assert "ESTABLISHED CONTEXT" not in str(plain[-1]["content"])


def test_markers_never_reach_the_reader_on_a_heading() -> None:
    # Headings carry no claim so they get no link, but the model marks them
    # anyway often enough that an unstripped marker reaches the reader as the
    # literal text "[[S1]]".
    renderer = CitationLineRenderer(
        [
            SourceBinding(
                source_id="S1",
                chunk=retrieved_chunk(chunk_id="paas/details/envs#add-envs:0"),
                defective=False,
            )
        ]
    )
    rendered = renderer.feed("## Using Liara CLI [[S1]]\nRun it. [[S1]]\n")

    assert not any("[[S1]]" in line for line in rendered)
    heading = next(line for line in rendered if line.startswith("## Using Liara CLI"))
    # The newline is load-bearing: without it the heading welds onto the next
    # paragraph and renders as one run-on line.
    assert heading.endswith("\n")
    assert heading == "## Using Liara CLI\n"
