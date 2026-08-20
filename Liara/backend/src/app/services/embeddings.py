from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import monotonic
from typing import Literal

import httpx
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from app.models.document_chunk import EMBEDDING_DIMENSIONS
from app.schemas.embedding import EmbeddingResponse

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"
CHAT_MODEL = "openai/gpt-5.6-luna"
DEFAULT_BATCH_SIZE = 32
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 524, 529}

Sleep = Callable[[float], Awaitable[None]]


class EmbeddingError(RuntimeError):
    """A safe embedding error that never contains provider payloads or credentials."""


class GenerationError(RuntimeError):
    """A safe generation error that never contains provider payloads or credentials."""


@dataclass(frozen=True)
class EmbeddingInput:
    key: str
    text: str


@dataclass(frozen=True)
class EmbeddedItem:
    key: str
    embedding: list[float]


@dataclass(frozen=True)
class EmbeddingBatch:
    items: list[EmbeddedItem]
    prompt_tokens: int
    total_tokens: int
    latency_seconds: float
    request_count: int = 1


@dataclass(frozen=True)
class ChatUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_write_input_tokens: int = 0
    reasoning_tokens: int = 0
    provider_cost_usd: float | None = None


@dataclass(frozen=True)
class ChatStreamEvent:
    kind: Literal["reasoning", "content", "usage", "finish"]
    text: str = ""
    usage: ChatUsage | None = None
    finish_reason: str | None = None


class OpenRouterClient:
    def __init__(
        self,
        api_key: SecretStr,
        *,
        http_client: httpx.AsyncClient | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_attempts: int = 4,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")

        self.batch_size = batch_size
        self.max_attempts = max_attempts
        self._sleep = sleep
        self._authorization_header = f"Bearer {api_key.get_secret_value()}"
        self._owns_http_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={"Content-Type": "application/json"},
        )

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_attempts: int = 4,
        sleep: Sleep = asyncio.sleep,
    ) -> OpenRouterClient:
        resolved_settings = settings or get_settings()
        api_key = resolved_settings.openrouter_api_key
        if api_key is None or not api_key.get_secret_value():
            raise EmbeddingError("OPENROUTER_API_KEY is required for embeddings")
        return cls(
            api_key,
            http_client=http_client,
            batch_size=batch_size,
            max_attempts=max_attempts,
            sleep=sleep,
        )

    async def __aenter__(self) -> OpenRouterClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_http_client:
            await self._http_client.aclose()

    async def iter_embeddings(
        self,
        inputs: Sequence[EmbeddingInput],
    ) -> AsyncIterator[EmbeddingBatch]:
        for start in range(0, len(inputs), self.batch_size):
            batch = inputs[start : start + self.batch_size]
            yield await self._embed_batch(batch)

    async def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatch:
        inputs = [EmbeddingInput(key=str(index), text=text) for index, text in enumerate(texts)]
        items: list[EmbeddedItem] = []
        prompt_tokens = 0
        total_tokens = 0
        latency_seconds = 0.0
        request_count = 0

        async for batch in self.iter_embeddings(inputs):
            items.extend(batch.items)
            prompt_tokens += batch.prompt_tokens
            total_tokens += batch.total_tokens
            latency_seconds += batch.latency_seconds
            request_count += batch.request_count

        return EmbeddingBatch(
            items=items,
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
            latency_seconds=latency_seconds,
            request_count=request_count,
        )

    async def _embed_batch(self, inputs: Sequence[EmbeddingInput]) -> EmbeddingBatch:
        started_at = monotonic()
        last_error = EmbeddingError("OpenRouter embedding request failed")

        for attempt in range(self.max_attempts):
            response: httpx.Response | None = None
            try:
                response = await self._http_client.post(
                    OPENROUTER_EMBEDDINGS_URL,
                    headers={"Authorization": self._authorization_header},
                    json={
                        "model": EMBEDDING_MODEL,
                        "input": [item.text for item in inputs],
                        "dimensions": EMBEDDING_DIMENSIONS,
                    },
                )
            except httpx.HTTPError:
                last_error = EmbeddingError("OpenRouter embedding request failed")
            else:
                if response.is_success:
                    try:
                        parsed = EmbeddingResponse.model_validate(response.json())
                        items = self._validated_items(parsed, inputs)
                    except ValidationError, ValueError:
                        last_error = EmbeddingError(
                            "OpenRouter returned an incomplete embedding batch"
                        )
                    else:
                        return EmbeddingBatch(
                            items=items,
                            prompt_tokens=parsed.usage.prompt_tokens,
                            total_tokens=parsed.usage.total_tokens,
                            latency_seconds=monotonic() - started_at,
                        )
                elif response.status_code not in TRANSIENT_STATUS_CODES:
                    raise EmbeddingError(
                        f"OpenRouter embedding request failed with status {response.status_code}"
                    )
                else:
                    last_error = EmbeddingError(
                        f"OpenRouter embedding request failed with status {response.status_code}"
                    )

            if attempt + 1 == self.max_attempts:
                raise last_error

            retry_after = _retry_after_seconds(response)
            exponential_delay = min(0.5 * (2**attempt), 8.0)
            await self._sleep(max(exponential_delay, retry_after))

        raise last_error  # pragma: no cover

    async def stream_chat(
        self,
        *,
        system_prompt: str,
        messages: Sequence[dict[str, object]],
        model: str = CHAT_MODEL,
        reasoning_effort: str = "high",
        max_tokens: int = 3000,
    ) -> AsyncIterator[ChatStreamEvent]:
        payload = chat_request_payload(
            system_prompt=system_prompt,
            messages=messages,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
        try:
            async with self._http_client.stream(
                "POST",
                OPENROUTER_CHAT_URL,
                headers={"Authorization": self._authorization_header},
                json=payload,
                timeout=httpx.Timeout(180.0),
            ) as response:
                if not response.is_success:
                    raise GenerationError(
                        f"OpenRouter generation request failed with status {response.status_code}"
                    )

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError as exc:
                        raise GenerationError(
                            "OpenRouter returned an invalid generation stream"
                        ) from exc
                    if not isinstance(event, dict) or event.get("error") is not None:
                        raise GenerationError("OpenRouter generation request failed")

                    usage = _chat_usage(event.get("usage"))
                    if usage is not None:
                        yield ChatStreamEvent(kind="usage", usage=usage)

                    choices = event.get("choices")
                    if not isinstance(choices, list) or not choices:
                        continue
                    choice = choices[0]
                    if not isinstance(choice, dict):
                        continue
                    delta = choice.get("delta")
                    if isinstance(delta, dict):
                        reasoning = _stream_text(delta.get("reasoning"))
                        if not reasoning:
                            reasoning = _stream_text(delta.get("reasoning_content"))
                        if reasoning:
                            yield ChatStreamEvent(kind="reasoning", text=reasoning)

                        content = _stream_text(delta.get("content"))
                        if content:
                            yield ChatStreamEvent(kind="content", text=content)

                    finish_reason = choice.get("finish_reason")
                    if isinstance(finish_reason, str):
                        yield ChatStreamEvent(
                            kind="finish",
                            finish_reason=finish_reason,
                        )
        except GenerationError:
            raise
        except httpx.HTTPError as exc:
            raise GenerationError("OpenRouter generation request failed") from exc

    @staticmethod
    def _validated_items(
        response: EmbeddingResponse,
        inputs: Sequence[EmbeddingInput],
    ) -> list[EmbeddedItem]:
        expected_indices = set(range(len(inputs)))
        actual_indices = {datum.index for datum in response.data}
        if actual_indices != expected_indices or len(response.data) != len(inputs):
            raise ValueError("embedding response indices do not match the request")

        ordered = sorted(response.data, key=lambda datum: datum.index)
        if any(len(datum.embedding) != EMBEDDING_DIMENSIONS for datum in ordered):
            raise ValueError("embedding response has the wrong dimensions")

        return [
            EmbeddedItem(key=inputs[datum.index].key, embedding=datum.embedding)
            for datum in ordered
        ]


class OpenRouterEmbeddingClient(OpenRouterClient):
    """Backward-compatible name for callers that only use embeddings."""


def chat_request_payload(
    *,
    system_prompt: str,
    messages: Sequence[dict[str, object]],
    model: str = CHAT_MODEL,
    reasoning_effort: str = "high",
    max_tokens: int = 3000,
) -> dict[str, object]:
    # Keep this insertion order deliberate. OpenRouter/OpenAI serialize tool
    # definitions before the stable system message, followed by volatile
    # conversation/context messages, which is the cache-friendly prefix order.
    return {
        "tools": [],
        "model": model,
        "reasoning": {"effort": reasoning_effort},
        "include_reasoning": True,
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
    }


def _stream_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _chat_usage(value: object) -> ChatUsage | None:
    if not isinstance(value, dict):
        return None
    prompt_details = value.get("prompt_tokens_details")
    completion_details = value.get("completion_tokens_details")
    cached_tokens = (
        prompt_details.get("cached_tokens", 0) if isinstance(prompt_details, dict) else 0
    )
    reasoning_tokens = (
        completion_details.get("reasoning_tokens", 0) if isinstance(completion_details, dict) else 0
    )
    provider_cost = value.get("cost")
    return ChatUsage(
        prompt_tokens=_integer(value.get("prompt_tokens")),
        completion_tokens=_integer(value.get("completion_tokens")),
        total_tokens=_integer(value.get("total_tokens")),
        cache_read_input_tokens=max(
            _integer(value.get("cache_read_input_tokens")),
            _integer(cached_tokens),
        ),
        cache_write_input_tokens=_integer(value.get("cache_write_input_tokens")),
        reasoning_tokens=_integer(reasoning_tokens),
        provider_cost_usd=float(provider_cost) if isinstance(provider_cost, int | float) else None,
    )


def _integer(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _retry_after_seconds(response: httpx.Response | None) -> float:
    if response is None:
        return 0.0
    value = response.headers.get("Retry-After")
    if not value:
        return 0.0
    try:
        return max(float(value), 0.0)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except TypeError, ValueError:
            return 0.0
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max((retry_at - datetime.now(UTC)).total_seconds(), 0.0)
