import json
from collections.abc import Awaitable

import httpx
import pytest
from pydantic import SecretStr

from app.models.document_chunk import EMBEDDING_DIMENSIONS
from app.services.embeddings import (
    EMBEDDING_MODEL,
    EmbeddingError,
    EmbeddingInput,
    OpenRouterEmbeddingClient,
)


def _response(indices: list[int], *, dimensions: int = EMBEDDING_DIMENSIONS) -> dict[str, object]:
    return {
        "data": [
            {
                "embedding": [float(index)] * dimensions,
                "index": index,
                "object": "embedding",
            }
            for index in indices
        ],
        "model": EMBEDDING_MODEL,
        "object": "list",
        "usage": {"prompt_tokens": len(indices) * 3, "total_tokens": len(indices) * 3},
    }


async def test_batches_requests_with_1024_dimensions() -> None:
    payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        payloads.append(payload)
        inputs = payload["input"]
        assert isinstance(inputs, list)
        return httpx.Response(200, json=_response(list(range(len(inputs)))))

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = OpenRouterEmbeddingClient(
        SecretStr("test-key"),
        http_client=http_client,
        batch_size=2,
    )
    result = await client.embed_texts(["one", "two", "three"])
    await http_client.aclose()

    assert [len(payload["input"]) for payload in payloads] == [2, 1]  # type: ignore[arg-type]
    assert all(payload["dimensions"] == 1024 for payload in payloads)
    assert all(payload["model"] == EMBEDDING_MODEL for payload in payloads)
    assert len(result.items) == 3
    assert result.total_tokens == 9


async def test_retries_rate_limits_and_incomplete_successes() -> None:
    calls = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "1.25"})
        if calls == 2:
            return httpx.Response(200, json=_response([0]))
        return httpx.Response(200, json=_response([0, 1]))

    def sleep(delay: float) -> Awaitable[None]:
        delays.append(delay)

        async def done() -> None:
            return None

        return done()

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = OpenRouterEmbeddingClient(
        SecretStr("test-key"),
        http_client=http_client,
        max_attempts=3,
        sleep=sleep,
    )
    result = await client.embed_texts(["one", "two"])
    await http_client.aclose()

    assert calls == 3
    assert delays == [1.25, 1.0]
    assert [item.key for item in result.items] == ["0", "1"]


async def test_completed_batches_survive_a_later_batch_failure() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json=_response([0]))
        return httpx.Response(529)

    async def no_sleep(delay: float) -> None:
        assert delay >= 0

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = OpenRouterEmbeddingClient(
        SecretStr("test-key"),
        http_client=http_client,
        batch_size=1,
        max_attempts=2,
        sleep=no_sleep,
    )
    completed: list[str] = []

    with pytest.raises(EmbeddingError):
        async for batch in client.iter_embeddings(
            [EmbeddingInput("first", "one"), EmbeddingInput("second", "two")]
        ):
            completed.extend(item.key for item in batch.items)
    await http_client.aclose()

    assert completed == ["first"]
