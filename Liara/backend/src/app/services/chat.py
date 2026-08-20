import asyncio
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from app.schemas.chat import ChatRequest

ChatChunk = dict[str, object]
PERSIAN_RE = re.compile(r"[\u0600-\u06ff]")


class ChatAnswerer(Protocol):
    def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]: ...


@dataclass(frozen=True)
class StubResponse:
    sources: list[dict[str, str]]
    reasoning: str
    answer: str
    notice: str


class StubChatAnswerer:
    """Fixture-shaped answerer that exercises the production streaming seam."""

    def __init__(self, delay_scale: float = 1.0) -> None:
        self.delay_scale = delay_scale

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        question = latest_user_text(request)
        is_persian = bool(PERSIAN_RE.search(question))
        response = select_stub_response(question, is_persian=is_persian)
        message_id = f"stub-{uuid4().hex}"
        reasoning_id = "reasoning-0"
        text_id = "text-0"

        yield {"type": "start", "messageId": message_id}
        yield status_chunk("understanding", is_persian=is_persian)
        await self.pause(0.22)

        yield status_chunk("retrieving", is_persian=is_persian)
        await self.pause(0.42)

        yield status_chunk("reading", is_persian=is_persian)
        await self.pause(0.52)
        yield {"type": "data-sources", "data": response.sources}
        yield {
            "type": "data-notice",
            "data": {"kind": "defect", "text": response.notice},
        }
        await self.pause(0.18)

        yield status_chunk("drafting", is_persian=is_persian)
        yield {"type": "reasoning-start", "id": reasoning_id}
        for token in chunk_text(response.reasoning, target_size=24):
            yield {"type": "reasoning-delta", "id": reasoning_id, "delta": token}
            await self.pause(0.08)
        yield {"type": "reasoning-end", "id": reasoning_id}

        yield {"type": "text-start", "id": text_id}
        for token in chunk_text(response.answer, target_size=18):
            yield {"type": "text-delta", "id": text_id, "delta": token}
            await self.pause(0.045)
        yield {"type": "text-end", "id": text_id}
        yield {"type": "finish", "finishReason": "stop"}

    async def pause(self, seconds: float) -> None:
        if self.delay_scale > 0:
            await asyncio.sleep(seconds * self.delay_scale)


def latest_user_text(request: ChatRequest) -> str:
    for message in reversed(request.messages):
        if message.role != "user":
            continue
        return "".join(
            text
            for part in message.parts
            if part.get("type") == "text" and isinstance((text := part.get("text")), str)
        )
    return ""


def status_chunk(phase: str, *, is_persian: bool) -> ChatChunk:
    labels = (
        {
            "understanding": "درک پرسش",
            "retrieving": "جست‌وجوی مستندات",
            "reading": "بررسی منابع",
            "drafting": "تدوین پاسخ",
        }
        if is_persian
        else {
            "understanding": "Understanding the question",
            "retrieving": "Searching Liara docs",
            "reading": "Reading the evidence",
            "drafting": "Drafting the answer",
        }
    )
    return {
        "type": "data-status",
        "data": {"phase": phase, "label": labels.get(phase, "Working")},
    }


def chunk_text(text: str, *, target_size: int) -> list[str]:
    chunks: list[str] = []
    cursor = 0
    while cursor < len(text):
        end = min(len(text), cursor + target_size)
        if end < len(text):
            next_space = text.find(" ", end)
            next_newline = text.find("\n", end)
            candidates = [position for position in (next_space, next_newline) if position != -1]
            if candidates:
                end = min(candidates) + 1
        chunks.append(text[cursor:end])
        cursor = end
    return chunks


def select_stub_response(question: str, *, is_persian: bool) -> StubResponse:
    normalized = question.casefold()
    if any(
        token in normalized
        for token in (
            "disk",
            "upload",
            "file",
            "دیسک",
            "فایل",
            "نگه‌داری",
            "نگهداری",
            "فضای ذخیره",
        )
    ):
        return disk_response(is_persian=is_persian)
    if any(token in normalized for token in ("gunicorn", "timeout", "تایم", "worker")):
        return timeout_response(is_persian=is_persian)
    return environment_response(is_persian=is_persian)


def environment_response(*, is_persian: bool) -> StubResponse:
    sources = [
        {
            "title": "متغیرهای محیطی در PaaS",
            "cite_url": "https://docs.liara.ir/paas/details/envs/#add-envs",
            "path": "paas/details/envs#add-envs",
        },
        {
            "title": "مرجع liara.json",
            "cite_url": "https://docs.liara.ir/paas/liarajson/",
            "path": "paas/liarajson",
        },
    ]
    if is_persian:
        return StubResponse(
            sources=sources,
            reasoning=(
                "مسیر استقرار را از مقدار متغیر جدا می‌کنم و فرمانی می‌دهم که "
                "نام متغیر و برنامه را صریح نگه دارد."
            ),
            answer=(
                "## تنظیم متغیر محیطی در لیارا\n\n"
                "برای یک برنامه‌ی موجود، متغیر را با CLI ثبت کنید؛ نام‌های لاتین مثل "
                "`GUNICORN_TIMEOUT` و فایل `liara.json` باید چپ‌به‌راست و جدا از متن "
                "فارسی نمایش داده شوند.\n\n"
                "```bash\n"
                "liara env:set GUNICORN_TIMEOUT=120 --app my-app\n"
                "```\n\n"
                "بعد از تغییر، یک استقرار تازه انجام دهید تا پردازه‌ی برنامه مقدار جدید "
                "را بگیرد. اگر از GitHub deploy استفاده می‌کنید، تنظیمات مخصوص همان مسیر "
                "را بررسی کنید و فیلدهای CLI را بی‌دلیل به `liara.json` اضافه نکنید.\n\n"
                "[راهنمای متغیرهای محیطی]"
                "(https://docs.liara.ir/paas/details/envs/#add-envs)"
            ),
            notice=(
                "صفحه مرجع liara.json همه فیلدهای استفاده‌شده در سایر صفحات مستندات، "
                "از جمله go.mainFile، را فهرست نمی‌کند."
            ),
        )
    return StubResponse(
        sources=sources,
        reasoning=(
            "I am separating the deploy path from the value itself, then giving a command "
            "that keeps the variable and app name explicit."
        ),
        answer=(
            "## Set an environment variable on Liara\n\n"
            "For an existing app, set the value with the CLI. Identifiers such as "
            "`GUNICORN_TIMEOUT` and `liara.json` stay directionally isolated in the UI.\n\n"
            "```bash\n"
            "liara env:set GUNICORN_TIMEOUT=120 --app my-app\n"
            "```\n\n"
            "Deploy again so the new process receives the value. If you deploy from GitHub, "
            "check the settings for that path instead of copying CLI-only fields into "
            "`liara.json`.\n\n"
            "[Environment variables guide]"
            "(https://docs.liara.ir/paas/details/envs/#add-envs)"
        ),
        notice=(
            "The liara.json reference omits some fields that are used elsewhere in the docs, "
            "including go.mainFile."
        ),
    )


def disk_response(*, is_persian: bool) -> StubResponse:
    sources = [
        {
            "title": "ساخت دیسک",
            "cite_url": "https://docs.liara.ir/paas/disks/create/",
            "path": "paas/disks/create",
        },
        {
            "title": "مسیر اتصال دیسک",
            "cite_url": "https://docs.liara.ir/paas/disks/route/",
            "path": "paas/disks/route",
        },
        {
            "title": "فایل‌سیستم برنامه",
            "cite_url": "https://docs.liara.ir/paas/details/file-system/",
            "path": "paas/details/file-system",
        },
    ]
    if is_persian:
        return StubResponse(
            sources=sources,
            reasoning=(
                "برای ماندگاری داده باید هم محدودیت فایل‌سیستم موقت را توضیح بدهم، "
                "هم ساخت دیسک و هم مسیر mount را کنار هم نگه دارم."
            ),
            answer=(
                "## برای داده‌ی ماندگار از دیسک استفاده کنید\n\n"
                "فایل‌سیستم خود برنامه موقتی است؛ داده‌ای که باید بعد از deploy باقی بماند "
                "را روی دیسک بنویسید. دیسک را بسازید و مسیر mount را با مسیر نوشتن برنامه "
                "یکسان کنید.\n\n"
                "```text\n"
                "/mnt/data\n"
                "```\n\n"
                "نوشتن در `/tmp` برای cache کوتاه‌عمر مناسب است، نه برای فایل کاربر یا "
                "پایگاه‌داده. [راهنمای ساخت دیسک]"
                "(https://docs.liara.ir/paas/disks/create/)"
            ),
            notice=(
                "راهنمای ماندگاری داده بین چند صفحه پخش شده است و یک صفحه به‌تنهایی "
                "کل مسیر ساخت و mount دیسک را پوشش نمی‌دهد."
            ),
        )
    return StubResponse(
        sources=sources,
        reasoning=(
            "A durable answer needs the ephemeral filesystem limit, disk creation, and the "
            "mount path together rather than treating them as separate facts."
        ),
        answer=(
            "## Use a disk for durable data\n\n"
            "The application filesystem is ephemeral. Put anything that must survive a deploy "
            "on a disk, and make the disk mount path match the path your app writes to.\n\n"
            "```text\n"
            "/mnt/data\n"
            "```\n\n"
            "Use `/tmp` only for short-lived cache, not uploads or a database. "
            "[Create a disk](https://docs.liara.ir/paas/disks/create/)"
        ),
        notice=(
            "Persistence guidance is split across multiple pages; no single page covers both "
            "disk creation and mount-path behavior."
        ),
    )


def timeout_response(*, is_persian: bool) -> StubResponse:
    sources = [
        {
            "title": "خطای Worker timeout",
            "cite_url": "https://docs.liara.ir/paas/fix-common-errors/worker-timeout/",
            "path": "paas/fix-common-errors/worker-timeout",
        },
        {
            "title": "متغیرهای محیطی",
            "cite_url": "https://docs.liara.ir/paas/details/envs/#add-envs",
            "path": "paas/details/envs#add-envs",
        },
    ]
    if is_persian:
        return StubResponse(
            sources=sources,
            reasoning=(
                "ابتدا تفاوت timeout واقعی با کندی عادی را روشن می‌کنم، سپس تغییر محدود "
                "و قابل بازگشت GUNICORN_TIMEOUT را پیشنهاد می‌دهم."
            ),
            answer=(
                "## رفع Worker timeout در Gunicorn\n\n"
                "اگر لاگ واقعاً عبارت `WORKER TIMEOUT` دارد، ابتدا endpoint کند را پیدا کنید. "
                "برای یک کاهش ریسک موقت می‌توانید timeout را کمی بالا ببرید:\n\n"
                "```bash\n"
                "liara env:set GUNICORN_TIMEOUT=120 --app my-app\n"
                "```\n\n"
                "این تغییر علت کندی را برطرف نمی‌کند؛ بعد از deploy دوباره زمان پاسخ و لاگ "
                "همان مسیر را بررسی کنید. [راهنمای Worker timeout]"
                "(https://docs.liara.ir/paas/fix-common-errors/worker-timeout/)"
            ),
            notice=(
                "صفحه Worker timeout نام GUNICORN_TIMEOUT را دارد اما نمونه‌ی کامل لاگ "
                "Gunicorn را نشان نمی‌دهد."
            ),
        )
    return StubResponse(
        sources=sources,
        reasoning=(
            "I will distinguish a real worker timeout from ordinary slowness, then suggest a "
            "bounded and reversible GUNICORN_TIMEOUT change."
        ),
        answer=(
            "## Handle a Gunicorn worker timeout\n\n"
            "If the log actually contains `WORKER TIMEOUT`, identify the slow endpoint first. "
            "As a temporary mitigation, raise the timeout by a bounded amount:\n\n"
            "```bash\n"
            "liara env:set GUNICORN_TIMEOUT=120 --app my-app\n"
            "```\n\n"
            "This does not fix the source of the latency. Deploy, then inspect the same route's "
            "latency and logs again. [Worker timeout guide]"
            "(https://docs.liara.ir/paas/fix-common-errors/worker-timeout/)"
        ),
        notice=(
            "The Worker timeout page names GUNICORN_TIMEOUT but does not include a complete "
            "Gunicorn log example."
        ),
    )


_stub_answerer = StubChatAnswerer()


def get_chat_answerer() -> ChatAnswerer:
    return _stub_answerer
