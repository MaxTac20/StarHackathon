import json
import logging
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient

from app.api.routes.chat import get_chat_answerer
from app.main import app
from app.schemas.chat import ChatRequest
from app.services.chat import ChatChunk


def parse_sse(text: str) -> list[object]:
    events: list[object] = []
    for block in text.split("\n\n"):
        if not block.startswith("data: "):
            continue
        data = block.removeprefix("data: ")
        events.append(data if data == "[DONE]" else json.loads(data))
    return events


def chat_payload(text: str = "چطور GUNICORN_TIMEOUT را تنظیم کنم؟") -> dict[str, object]:
    return {
        "id": "chat-test",
        "trigger": "submit-message",
        "messages": [
            {
                "id": "user-1",
                "role": "user",
                "parts": [{"type": "text", "text": text}],
            }
        ],
    }


class ScriptedAnswerer:
    async def stream(self, _request: ChatRequest) -> AsyncIterator[ChatChunk]:
        yield {"type": "start", "messageId": "scripted"}
        for phase in ("understanding", "retrieving", "reading"):
            yield {
                "type": "data-status",
                "data": {"phase": phase, "label": phase},
            }
        yield {
            "type": "data-sources",
            "data": [
                {
                    "title": "متغیرهای محیطی",
                    "cite_url": "https://docs.liara.ir/paas/details/envs/#add-envs",
                    "path": "paas/details/envs#add-envs",
                }
            ],
        }
        yield {
            "type": "data-status",
            "data": {"phase": "drafting", "label": "drafting"},
        }
        yield {"type": "reasoning-start", "id": "reasoning-0"}
        yield {
            "type": "reasoning-delta",
            "id": "reasoning-0",
            "delta": "Checking the retrieved source.",
        }
        yield {"type": "reasoning-end", "id": "reasoning-0"}
        yield {"type": "text-start", "id": "text-0"}
        yield {
            "type": "text-delta",
            "id": "text-0",
            "delta": "Use the documented environment-variable flow.",
        }
        yield {"type": "text-end", "id": "text-0"}
        yield {"type": "finish", "finishReason": "stop"}


async def test_chat_stream_matches_ui_message_protocol(client: AsyncClient) -> None:
    app.dependency_overrides[get_chat_answerer] = lambda: ScriptedAnswerer()

    response = await client.post("/api/chat", json=chat_payload())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"

    events = parse_sse(response.text)
    event_types = [event["type"] for event in events if isinstance(event, dict)]
    assert event_types[0:2] == ["start", "data-status"]
    assert [
        event["data"]["phase"]
        for event in events
        if isinstance(event, dict) and event.get("type") == "data-status"
    ] == ["understanding", "retrieving", "reading", "drafting"]
    assert event_types.index("data-sources") < event_types.index("reasoning-start")
    assert event_types.index("reasoning-end") < event_types.index("text-start")
    assert events[-1] == "[DONE]"


class ExplodingAnswerer:
    async def stream(self, _request: ChatRequest) -> AsyncIterator[ChatChunk]:
        yield {
            "type": "data-status",
            "data": {"phase": "understanding", "label": "Understanding"},
        }
        raise RuntimeError("provider payload sk-live-secret-fragment traceback")


async def test_unhandled_answerer_error_is_safe_in_stream_and_log(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app.dependency_overrides[get_chat_answerer] = lambda: ExplodingAnswerer()

    with caplog.at_level(logging.ERROR):
        response = await client.post("/api/chat", json=chat_payload("hello"))

    events = parse_sse(response.text)
    error = next(
        event for event in events if isinstance(event, dict) and event.get("type") == "error"
    )
    assert error == {
        "type": "error",
        "errorText": "The answer could not be completed. Please try again.",
    }
    assert events[-1] == "[DONE]"
    assert "sk-live-secret-fragment" not in response.text
    assert "sk-live-secret-fragment" not in caplog.text
    assert "traceback" not in response.text.lower()
    assert "traceback" not in caplog.text.lower()
