import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.chat import ChatAnswerer, ChatChunk, get_chat_answerer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

SAFE_STREAM_ERROR = "The answer could not be completed. Please try again."


def sse_event(payload: ChatChunk) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n\n"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    answerer: Annotated[ChatAnswerer, Depends(get_chat_answerer)],
) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        try:
            async for chunk in answerer.stream(request):
                yield sse_event(chunk)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Chat answer stream failed")
            yield sse_event({"type": "error", "errorText": SAFE_STREAM_ERROR})
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "x-vercel-ai-ui-message-stream": "v1",
        },
    )
