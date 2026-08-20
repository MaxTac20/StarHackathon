from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import monotonic

import httpx
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from app.models.document_chunk import EMBEDDING_DIMENSIONS
from app.schemas.embedding import EmbeddingResponse

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"
DEFAULT_BATCH_SIZE = 32
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 524, 529}

Sleep = Callable[[float], Awaitable[None]]


class EmbeddingError(RuntimeError):
    """A safe embedding error that never contains provider payloads or credentials."""


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


class OpenRouterEmbeddingClient:
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
    ) -> OpenRouterEmbeddingClient:
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

    async def __aenter__(self) -> OpenRouterEmbeddingClient:
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
