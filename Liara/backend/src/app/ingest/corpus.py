from __future__ import annotations

import html
import json
import math
import re
from collections import Counter, defaultdict, deque
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urldefrag, urljoin

from app.ingest.casts import CastSnippet, extract_cast_snippets
from app.ingest.models import CodeBlockRecord, CorpusRecord, ManifestInventory, ManifestKey
from app.ingest.redact import redact_credentials
from app.utils.persian import normalize

TARGET_TOKENS = 400
MAX_TOKENS = 500
TOKENS_PER_WORD = 3.45
SKIPPED_PAGE = "ai/ai-sdk-ui/chatbot"

# Qwen3's 1024-dimensional Matryoshka vectors are most useful on focused topical
# units, not whole pages. At the measured 3.45 tokens per Persian whitespace word,
# 400 tokens is about 116 words: enough for an explanation plus code while leaving
# room to retrieve several chunks. The 500-token packing ceiling absorbs breadcrumbs.

_ORIGINAL_LINK = re.compile(r"^Original link:\s*(\S+)\s*$")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
_SECTION = re.compile(r"<Section\b(?P<attrs>[^>]*)/?>", re.DOTALL)
_ATTRIBUTE = re.compile(r"""\b(id|title)\s*=\s*(["'])(.*?)\2""", re.DOTALL)
_ASCIINEMA = re.compile(r"""<Asciinema\s+id=["']([^"']+)["']\s*/>""")
_JSX_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
_MARKDOWN_TARGET = re.compile(r"(\]\()([^)]+)(\))")
_REFERENCE_LINK = re.compile(r"^(\s*\[[^\]]+\]:\s*)(\S+)(.*)$")
_HTML_LINK = re.compile(r"""(\b(?:href|src)=["'])([^"']+)(["'])""")
_INLINE_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
_MDX_TAG = re.compile(r"<[^>]+>")
_MARKUP = re.compile(r"[`*_~<>]")
_WHITESPACE = re.compile(r"\s+")
_SENTENCE_BREAK = re.compile(r"(?<=[.!؟؛])\s+|\n+")
_SHELL_COMMAND = re.compile(
    r"^(?:\$\s*)?(?:"
    r"liara|npm|npx|pnpm|yarn|node|uv|pip|python3?|git|docker|curl|wget|"
    r"ssh|scp|rclone|redis-cli|mongo(?:restore)?|mysql|pg_restore|sqlcmd|"
    r"touch|mkdir|cd|echo|cat|export|source|bash|sh|sudo|apt(?:-get)?|"
    r"systemctl|ls(?:blk)?|lvdisplay|lvchange|lvremove|vgremove|pvremove|"
    r"umount|fuser|lsof|go|dotnet|php|composer"
    r")(?:\s|$)"
)

_LANG_ALIASES = {
    "": "text",
    "console": "bash",
    "javascript": "js",
    "shell": "bash",
    "sh": "bash",
    "typescript": "ts",
    "yml": "yaml",
    "zsh": "bash",
}

# This is a shape filter, not the inventory itself. It rejects package.json, API
# responses, and arbitrary JSON while nested paths remain fully observed from data.
_LIARA_JSON_ROOTS = {
    "account",
    "angular",
    "app",
    "args",
    "build",
    "cron",
    "disks",
    "django",
    "docker",
    "dotnet",
    "flask",
    "go",
    "healthCheck",
    "image",
    "laravel",
    "next",
    "node",
    "php",
    "platform",
    "port",
    "python",
    "react",
    "team-id",
    "vue",
}


@dataclass(frozen=True)
class SectionAnchor:
    title: str
    anchor: str


@dataclass(frozen=True)
class CastReference:
    cast_id: str
    context: str
    anchor_scope: str | None


@dataclass
class PageSection:
    heading_path: list[str]
    anchor: str | None
    body_lines: list[str] = field(default_factory=list)
    casts: list[CastSnippet] = field(default_factory=list)


@dataclass(frozen=True)
class Fence:
    label: str
    body: str


@dataclass(frozen=True)
class AtomicBlock:
    text: str
    code_blocks: list[CodeBlockRecord]


@dataclass
class IngestReport:
    cast_snippets_by_id: dict[str, int] = field(default_factory=dict)
    empty_cast_ids: set[str] = field(default_factory=set)
    redactions_by_page: Counter[str] = field(default_factory=Counter)
    redactions_by_shape: Counter[str] = field(default_factory=Counter)

    @property
    def redaction_count(self) -> int:
        return self.redactions_by_page.total()


def build_records(
    corpus_dir: Path, *, commit: str, report: IngestReport | None = None
) -> list[CorpusRecord]:
    mirror_root = corpus_dir / "public" / "llms"
    mdx_root = corpus_dir / "src" / "pages"
    cast_root = corpus_dir / "public" / "casts"
    records: list[CorpusRecord] = []
    casts = _load_casts(cast_root, report)

    mirror_paths = sorted(mirror_root.rglob("*.md"))
    mdx_paths = sorted(mdx_root.rglob("*.mdx"))
    if len(mirror_paths) != len(mdx_paths):
        raise ValueError(f"mirror/MDX page count differs: {len(mirror_paths)} != {len(mdx_paths)}")

    for mirror_path in mirror_paths:
        relative = mirror_path.relative_to(mirror_root).with_suffix("")
        page_path = relative.as_posix()
        if page_path == SKIPPED_PAGE:
            continue

        mdx_path = (mdx_root / relative).with_suffix(".mdx")
        if not mdx_path.is_file():
            raise ValueError(f"missing MDX pair for {page_path}")

        markdown = mirror_path.read_text(encoding="utf-8-sig")
        mdx = mdx_path.read_text(encoding="utf-8-sig")
        url, sections = parse_page(markdown, extract_section_anchors(mdx))
        if not sections:
            continue
        attach_casts(
            sections,
            extract_cast_references(mdx),
            casts,
        )
        records.extend(_chunk_page(page_path, url, sections, commit, report=report))

    return records


def build_manifest(corpus_dir: Path, *, commit: str) -> ManifestInventory:
    mirror_root = corpus_dir / "public" / "llms"
    frequencies: Counter[str] = Counter()
    pages: dict[str, set[str]] = defaultdict(set)

    for mirror_path in sorted(mirror_root.rglob("*.md")):
        page_path = mirror_path.relative_to(mirror_root).with_suffix("").as_posix()
        if page_path == SKIPPED_PAGE:
            continue
        markdown = mirror_path.read_text(encoding="utf-8-sig")
        for fence in iter_fences(markdown):
            try:
                value = json.loads(fence.body)
            except json.JSONDecodeError:
                continue
            if not _is_liara_json_object(value):
                continue
            for key_path in set(_flatten_leaf_paths(value)):
                frequencies[key_path] += 1
                pages[key_path].add(page_path)

    keys = [
        ManifestKey(
            path=key_path,
            frequency=frequencies[key_path],
            example_pages=sorted(pages[key_path])[:5],
        )
        for key_path in sorted(frequencies)
    ]
    return ManifestInventory(commit=commit, keys=keys)


def extract_section_anchors(mdx: str) -> list[SectionAnchor]:
    anchors: list[SectionAnchor] = []
    for section_match in _SECTION.finditer(_JSX_COMMENT.sub("", mdx)):
        attributes = {
            name: value for name, _, value in _ATTRIBUTE.findall(section_match.group("attrs"))
        }
        if "id" in attributes and "title" in attributes:
            anchors.append(SectionAnchor(title=attributes["title"], anchor=attributes["id"]))
    return anchors


def extract_cast_references(mdx: str) -> list[CastReference]:
    active_mdx = _JSX_COMMENT.sub("", mdx)
    references: list[CastReference] = []
    section_matches = list(_SECTION.finditer(active_mdx))
    for match in _ASCIINEMA.finditer(active_mdx):
        preceding_section = next(
            (section for section in reversed(section_matches) if section.start() < match.start()),
            None,
        )
        attributes = (
            {name: value for name, _, value in _ATTRIBUTE.findall(preceding_section.group("attrs"))}
            if preceding_section is not None
            else {}
        )
        references.append(
            CastReference(
                cast_id=match.group(1),
                context=_preceding_visible_context(active_mdx[: match.start()]),
                anchor_scope=attributes.get("id"),
            )
        )
    return references


def parse_page(
    markdown: str, section_anchors: Sequence[SectionAnchor]
) -> tuple[str, list[PageSection]]:
    lines = markdown.splitlines()
    if not lines:
        raise ValueError("empty mirror page")

    original_match = _ORIGINAL_LINK.fullmatch(lines[0].lstrip("\ufeff"))
    if original_match is None:
        raise ValueError("mirror page does not start with an Original link header")
    url = original_match.group(1)

    anchors_by_title: dict[str, deque[str]] = defaultdict(deque)
    for item in section_anchors:
        anchors_by_title[_heading_key(item.title)].append(item.anchor)

    stack: list[tuple[int, str, str | None]] = []
    sections: list[PageSection] = []
    current: PageSection | None = None
    in_fence = False
    fence_char = ""

    for line in lines[1:]:
        fence_match = _FENCE_OPEN.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
            elif marker[0] == fence_char:
                in_fence = False

        heading_match = None if in_fence else _HEADING.fullmatch(line)
        if heading_match is None:
            if current is not None:
                current.body_lines.append(line)
            continue

        level = len(heading_match.group(1))
        title = heading_match.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        if _heading_key(title) == "all links":
            current = None
            continue

        title_queue = anchors_by_title[_heading_key(title)]
        direct_anchor = title_queue.popleft() if title_queue else None
        inherited_anchor = direct_anchor or next(
            (anchor for _, _, anchor in reversed(stack) if anchor is not None), None
        )
        stack.append((level, title, direct_anchor))
        current = PageSection(
            heading_path=[item[1] for item in stack],
            anchor=inherited_anchor,
        )
        sections.append(current)

    return url, sections


def attach_casts(
    sections: Sequence[PageSection],
    references: Sequence[CastReference],
    casts: Mapping[str, Sequence[CastSnippet]],
) -> None:
    searchable = [
        _search_text(" ".join(section.heading_path + section.body_lines)) for section in sections
    ]
    for reference in references:
        if reference.cast_id not in casts:
            raise ValueError(f"missing cast file: {reference.cast_id}")
        snippets = casts[reference.cast_id]
        if not snippets:
            continue
        scoped_indices = [
            index
            for index, section in enumerate(sections)
            if section.anchor == reference.anchor_scope
        ]
        candidate_indices = scoped_indices or list(range(len(sections)))
        scoped_searchable = [searchable[index] for index in candidate_indices]
        scoped_target = _best_cast_section(scoped_searchable, reference.context, snippets)
        target = candidate_indices[scoped_target]
        sections[target].casts.extend(snippets)


def _load_casts(cast_root: Path, report: IngestReport | None) -> dict[str, list[CastSnippet]]:
    casts: dict[str, list[CastSnippet]] = {}
    for cast_path in sorted(cast_root.glob("*.cast")):
        cast_id = cast_path.stem
        snippets = extract_cast_snippets(cast_path)
        casts[cast_id] = snippets
        if report is None:
            continue
        if snippets:
            report.cast_snippets_by_id[cast_id] = len(snippets)
        else:
            report.empty_cast_ids.add(cast_id)
    return casts


def iter_fences(markdown: str) -> Iterator[Fence]:
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        opening = _FENCE_OPEN.match(lines[index])
        if opening is None:
            index += 1
            continue
        marker = opening.group(1)
        label = opening.group(2).strip().split(maxsplit=1)[0] if opening.group(2).strip() else ""
        body: list[str] = []
        index += 1
        while index < len(lines):
            closing = _FENCE_OPEN.match(lines[index])
            if (
                closing is not None
                and closing.group(1)[0] == marker[0]
                and len(closing.group(1)) >= len(marker)
                and not closing.group(2).strip()
            ):
                break
            body.append(lines[index])
            index += 1
        yield Fence(label=label, body="\n".join(body).strip())
        index += 1


def sniff_fence_language(label: str, body: str) -> str:
    try:
        json.loads(body)
    except json.JSONDecodeError:
        pass
    else:
        return "json"

    first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    if first_line.startswith("#!") or _SHELL_COMMAND.match(first_line):
        return "bash"

    normalized_label = label.lower().strip("{}")
    if normalized_label == "json":
        return "text"
    return _LANG_ALIASES.get(normalized_label, normalized_label or "text")


def estimate_tokens(text: str) -> int:
    words = len(re.findall(r"\S+", text))
    return max(1, math.ceil(words * TOKENS_PER_WORD))


def _chunk_page(
    page_path: str,
    url: str,
    sections: Sequence[PageSection],
    commit: str,
    *,
    report: IngestReport | None = None,
) -> list[CorpusRecord]:
    records: list[CorpusRecord] = []
    ordinals: Counter[str] = Counter()

    for section in sections:
        atoms = _section_atoms(section, url, page_path=page_path, report=report)
        packs = _pack_atoms(section.heading_path, atoms)
        identity = section.anchor or "page"
        for pack in packs:
            ordinal = ordinals[identity]
            ordinals[identity] += 1
            text = _render_chunk_text(section.heading_path, pack)
            records.append(
                CorpusRecord(
                    id=f"{page_path}#{identity}:{ordinal}",
                    path=page_path,
                    url=url,
                    anchor=section.anchor,
                    cite_url=(
                        f"{urldefrag(url).url}#{section.anchor}"
                        if section.anchor is not None
                        else urldefrag(url).url
                    ),
                    heading_path=section.heading_path,
                    lang="fa",
                    text=text,
                    text_norm=normalize(text),
                    code_blocks=[code_block for atom in pack for code_block in atom.code_blocks],
                    token_estimate=estimate_tokens(text),
                    commit=commit,
                )
            )
    return records


def _section_atoms(
    section: PageSection,
    page_url: str,
    *,
    page_path: str,
    report: IngestReport | None,
) -> list[AtomicBlock]:
    atoms: list[AtomicBlock] = []
    lines = section.body_lines
    index = 0
    prose: list[str] = []

    def flush_prose() -> None:
        if not prose:
            return
        text = "\n".join(prose).strip()
        prose.clear()
        if text:
            rewritten = _rewrite_relative_links(text, page_url)
            atoms.extend(_split_prose_atom(rewritten))

    while index < len(lines):
        opening = _FENCE_OPEN.match(lines[index])
        if opening is not None:
            flush_prose()
            marker = opening.group(1)
            raw_label = opening.group(2).strip()
            label = raw_label.split(maxsplit=1)[0] if raw_label else ""
            opening_line = lines[index]
            closing_line: str | None = None
            body: list[str] = []
            index += 1
            while index < len(lines):
                closing = _FENCE_OPEN.match(lines[index])
                if (
                    closing is not None
                    and closing.group(1)[0] == marker[0]
                    and len(closing.group(1)) >= len(marker)
                    and not closing.group(2).strip()
                ):
                    closing_line = lines[index]
                    break
                body.append(lines[index])
                index += 1
            redaction = redact_credentials("\n".join(body))
            _record_redactions(report, page_path, redaction.counts_by_shape)
            code_text = redaction.text.strip()
            fence_lines = [opening_line, *redaction.text.splitlines()]
            if closing_line is not None:
                fence_lines.append(closing_line)
            atoms.append(
                AtomicBlock(
                    text="\n".join(fence_lines).strip(),
                    code_blocks=[
                        CodeBlockRecord(
                            lang=sniff_fence_language(label, code_text),
                            source="fence",
                            text=code_text,
                        )
                    ],
                )
            )
        elif not lines[index].strip():
            flush_prose()
        else:
            prose.append(lines[index])
        index += 1
    flush_prose()

    for snippet in section.casts:
        redaction = redact_credentials(snippet.text)
        _record_redactions(report, page_path, redaction.counts_by_shape)
        atoms.append(
            AtomicBlock(
                text=f"```console\n{redaction.text}\n```",
                code_blocks=[CodeBlockRecord(lang="bash", source="cast", text=redaction.text)],
            )
        )
    return atoms


def _record_redactions(
    report: IngestReport | None, page_path: str, counts_by_shape: Mapping[str, int]
) -> None:
    if report is not None and counts_by_shape:
        report.redactions_by_page[page_path] += sum(counts_by_shape.values())
        report.redactions_by_shape.update(counts_by_shape)


def _split_prose_atom(text: str) -> list[AtomicBlock]:
    if estimate_tokens(text) <= MAX_TOKENS:
        return [AtomicBlock(text=text, code_blocks=[])]

    pieces = [piece.strip() for piece in _SENTENCE_BREAK.split(text) if piece.strip()]
    if len(pieces) == 1:
        words = text.split()
        words_per_piece = max(1, int(TARGET_TOKENS / TOKENS_PER_WORD))
        pieces = [
            " ".join(words[index : index + words_per_piece])
            for index in range(0, len(words), words_per_piece)
        ]
    return [AtomicBlock(text=piece, code_blocks=[]) for piece in pieces]


def _pack_atoms(
    heading_path: Sequence[str], atoms: Sequence[AtomicBlock]
) -> list[list[AtomicBlock]]:
    if not atoms:
        return [[]]

    packs: list[list[AtomicBlock]] = []
    current: list[AtomicBlock] = []
    for atom in atoms:
        candidate = [*current, atom]
        if current and estimate_tokens(_render_chunk_text(heading_path, candidate)) > MAX_TOKENS:
            packs.append(current)
            current = [atom]
        else:
            current = candidate

        if estimate_tokens(_render_chunk_text(heading_path, current)) >= TARGET_TOKENS:
            packs.append(current)
            current = []

    if current:
        packs.append(current)
    return packs


def _render_chunk_text(heading_path: Sequence[str], atoms: Sequence[AtomicBlock]) -> str:
    breadcrumb = "\n".join(
        f"{'#' * min(level, 6)} {title}" for level, title in enumerate(heading_path, start=1)
    )
    body = "\n\n".join(atom.text for atom in atoms if atom.text)
    return f"{breadcrumb}\n\n{body}".strip()


def _rewrite_relative_links(text: str, page_url: str) -> str:
    def markdown_replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}{_absolute_target(match.group(2), page_url)}{match.group(3)}"

    def reference_replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}{_absolute_target(match.group(2), page_url)}{match.group(3)}"

    def html_replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}{_absolute_target(match.group(2), page_url)}{match.group(3)}"

    rewritten = _MARKDOWN_TARGET.sub(markdown_replacement, text)
    rewritten = "\n".join(
        _REFERENCE_LINK.sub(reference_replacement, line) for line in rewritten.splitlines()
    )
    return _HTML_LINK.sub(html_replacement, rewritten)


def _absolute_target(target: str, page_url: str) -> str:
    if target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return target
    return urljoin(page_url, target)


def _heading_key(title: str) -> str:
    without_links = _INLINE_LINK.sub(lambda match: match.group(1), html.unescape(title))
    return normalize(_MARKUP.sub("", without_links))


def _preceding_visible_context(prefix: str) -> str:
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", prefix, re.DOTALL)
    raw = paragraphs[-1] if paragraphs else prefix[-1200:]
    raw = _MDX_TAG.sub(" ", raw)
    raw = re.sub(r"\{`(.*?)`\}", r"\1", raw, flags=re.DOTALL)
    raw = re.sub(r"\{[^{}]*\}", " ", raw)
    return _WHITESPACE.sub(" ", html.unescape(raw)).strip()


def _best_cast_section(
    searchable_sections: Sequence[str],
    context: str,
    snippets: Sequence[CastSnippet],
) -> int:
    context_text = _search_text(context)
    commands = [_search_text(snippet.command) for snippet in snippets]
    scores = [
        _cast_match_score(searchable, context_text, commands) for searchable in searchable_sections
    ]
    return max(range(len(scores)), key=scores.__getitem__)


def _cast_match_score(searchable: str, context: str, commands: Sequence[str]) -> int:
    score = 0
    context_words = [word for word in context.split() if len(word) > 2]
    if context and context in searchable:
        score += 200
    score += sum(1 for word in set(context_words) if word in searchable)

    for command in commands:
        command_words = command.split()
        signature = " ".join(command_words[:2])
        if command and command in searchable:
            score += 300
        elif signature and signature in searchable:
            score += 120
        elif command_words and command_words[0] in searchable:
            score += 30
    return score


def _search_text(text: str) -> str:
    return normalize(re.sub(r"[^\w\u0600-\u06ff]+", " ", text))


def _is_liara_json_object(value: object) -> bool:
    return (
        isinstance(value, dict)
        and bool(value)
        and all(isinstance(key, str) for key in value)
        and set(value).issubset(_LIARA_JSON_ROOTS)
    )


def _flatten_leaf_paths(value: object, prefix: str = "") -> Iterable[str]:
    if isinstance(value, Mapping):
        if not value and prefix:
            yield prefix
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _flatten_leaf_paths(child, child_prefix)
    elif isinstance(value, list):
        if not value and prefix:
            yield prefix
        contains_nested = False
        for child in value:
            if isinstance(child, (Mapping, list)):
                contains_nested = True
                yield from _flatten_leaf_paths(child, prefix)
        if not contains_nested and prefix:
            yield prefix
    elif prefix:
        yield prefix
