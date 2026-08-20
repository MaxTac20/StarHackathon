import json
from collections.abc import AsyncIterator

from httpx import AsyncClient

from app.main import app
from app.schemas.chat import ChatRequest
from app.services.chat import ChatChunk, StubChatAnswerer, get_chat_answerer


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


async def test_chat_stream_matches_ui_message_protocol(client: AsyncClient) -> None:
    app.dependency_overrides[get_chat_answerer] = lambda: StubChatAnswerer(delay_scale=0)

    response = await client.post("/api/chat", json=chat_payload())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"

    events = parse_sse(response.text)
    event_types = [event["type"] for event in events if isinstance(event, dict) and "type" in event]
    assert event_types[0:2] == ["start", "data-status"]
    assert [
        event["data"]["phase"]
        for event in events
        if isinstance(event, dict) and event.get("type") == "data-status"
    ] == ["understanding", "retrieving", "reading", "drafting"]
    assert event_types.index("data-sources") < event_types.index("reasoning-start")
    assert event_types.index("reasoning-end") < event_types.index("text-start")
    assert "data-notice" in event_types
    assert events[-1] == "[DONE]"


async def test_file_persistence_suggestion_returns_disk_guidance(client: AsyncClient) -> None:
    app.dependency_overrides[get_chat_answerer] = lambda: StubChatAnswerer(delay_scale=0)

    response = await client.post(
        "/api/chat",
        json=chat_payload("برای نگه‌داری فایل‌ها بعد از deploy چه کار کنم؟"),
    )

    events = parse_sse(response.text)
    sources = next(
        event["data"]
        for event in events
        if isinstance(event, dict) and event.get("type") == "data-sources"
    )
    assert sources[0]["cite_url"] == "https://docs.liara.ir/paas/disks/create/"
    assert any(
        isinstance(event, dict) and event.get("type") == "text-delta" and "دیسک" in event["delta"]
        for event in events
    )


class ExplodingAnswerer:
    async def stream(self, _request: ChatRequest) -> AsyncIterator[ChatChunk]:
        yield {
            "type": "data-status",
            "data": {"phase": "understanding", "label": "Understanding"},
        }
        raise RuntimeError("provider payload sk-live-secret-fragment traceback")


async def test_unhandled_answerer_error_is_safe_and_terminates(client: AsyncClient) -> None:
    app.dependency_overrides[get_chat_answerer] = lambda: ExplodingAnswerer()

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
    assert "traceback" not in response.text.lower()
