from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyte
from pyte.screens import Char

_PROMPTS = (
    re.compile(r"^➜\s+\S+\s+(?P<command>.+)$"),
    re.compile(r"^(?:\$|~)\s+(?P<command>.+)$"),
    re.compile(r"^[^\s@]+@[^\s:]+:[^#$]*[#$]\s+(?P<command>.+)$"),
    re.compile(r"^[A-Za-z0-9_.-]+\$\s+(?P<command>.+)$"),
    re.compile(r"^PS\s+[^>]+>\s+(?P<command>.+)$"),
    re.compile(r"^(?:MySQL|MariaDB|MongoDB)(?:\s+\[[^]]*\])?>\s+(?P<command>.+)$"),
    re.compile(r"^\d+>\s+(?P<command>.+)$"),
)
_EMPTY_PROMPTS = (
    re.compile(r"^➜\s+\S+\s*$"),
    re.compile(r"^(?:\$|~)\s*$"),
    re.compile(r"^[^\s@]+@[^\s:]+:[^#$]*[#$]\s*$"),
    re.compile(r"^[A-Za-z0-9_.-]+\$\s*$"),
    re.compile(r"^PS\s+[^>]+>\s*$"),
    re.compile(r"^(?:MySQL|MariaDB|MongoDB)(?:\s+\[[^]]*\])?>\s*$"),
    re.compile(r"^\d+>\s*$"),
)
_COMMAND_PREFIX = re.compile(
    r"^(?:"
    r"liara|lvextend|vgextend|sudo|ssh|echo|ls|mongo|mongorestore|redis-cli|"
    r"mysql|mariadb|fdisk|pvcreate|mkfs(?:\.[a-z0-9]+)?|resize2fs|npm|printf|cat|"
    r"sqlcmd|pg_restore|rclone|lvremove|sh|rdb|df|resolvectl|lsblk|vgdisplay|umount|"
    r"pvremove|ip|CREATE|GRANT|FLUSH|SELECT|INSERT|UPDATE|DELETE|:(?:help|quit)"
    r")(?:\s|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CastSnippet:
    command: str
    result: str

    @property
    def text(self) -> str:
        return f"{self.command}\n{self.result}".rstrip()


@dataclass(frozen=True)
class _ScreenLine:
    text: str
    reaches_right_edge: bool
    space_at_right_edge: bool
    first_character_bold: bool
    first_character_foreground: str


def extract_cast_snippets(path: Path) -> list[CastSnippet]:
    """Replay output events and split the final terminal screen into commands."""
    columns, lines, events = _read_cast(path)
    screen = pyte.HistoryScreen(columns, lines, history=10_000)
    stream = pyte.Stream(screen)
    for data in events:
        stream.feed(data)

    rendered = _screen_lines(screen, columns)
    snippets: list[CastSnippet] = []
    command: str | None = None
    output: list[str] = []
    index = 0
    while index < len(rendered):
        line = rendered[index]
        is_prompt, next_command = _parse_prompt(line)
        if is_prompt:
            _append_snippet(snippets, command, output)
            output = []
            command = next_command
            while command is not None and index + 1 < len(rendered):
                following = rendered[index + 1]
                following_is_prompt, _ = _parse_prompt(following)
                continues = line.reaches_right_edge or following.text.startswith(("-", "<", "|"))
                if following_is_prompt or not continues:
                    break
                index += 1
                needs_space = line.space_at_right_edge or following.text.startswith(("-", "<", "|"))
                separator = " " if needs_space else ""
                command += f"{separator}{following.text.strip()}"
                line = following
        elif command is not None:
            output.append(line.text)
        index += 1

    _append_snippet(snippets, command, output)
    return snippets


def _read_cast(path: Path) -> tuple[int, int, list[str]]:
    rows = path.read_text(encoding="utf-8").splitlines()
    if not rows:
        raise ValueError(f"empty cast file: {path.name}")
    try:
        header: Any = json.loads(rows[0])
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid cast header: {path.name}") from error
    if not isinstance(header, dict):
        raise ValueError(f"invalid cast header: {path.name}")
    columns = header.get("width")
    lines = header.get("height")
    if not isinstance(columns, int) or columns <= 0 or not isinstance(lines, int) or lines <= 0:
        raise ValueError(f"invalid cast dimensions: {path.name}")

    events: list[str] = []
    for row in rows[1:]:
        try:
            event: Any = json.loads(row)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(event, list)
            and len(event) == 3
            and event[1] == "o"
            and isinstance(event[2], str)
        ):
            events.append(event[2])
    return columns, lines, events


def _screen_lines(screen: pyte.HistoryScreen, columns: int) -> list[_ScreenLine]:
    buffer_lines = [*screen.history.top, *(screen.buffer[y] for y in range(screen.lines))]
    rendered = [_render_line(line, columns) for line in buffer_lines]
    while rendered and not rendered[0].text:
        rendered.pop(0)
    while rendered and not rendered[-1].text:
        rendered.pop()
    return rendered


def _render_line(line: Mapping[int, Char], columns: int) -> _ScreenLine:
    text = "".join(line[x].data if x in line else " " for x in range(columns)).rstrip()
    right_edge = line[columns - 1].data if columns - 1 in line else None
    reaches_right_edge = len(text) >= columns - 1 or right_edge not in {None, " "}
    return _ScreenLine(
        text=text,
        reaches_right_edge=reaches_right_edge,
        space_at_right_edge=right_edge == " ",
        first_character_bold=bool(line[0].bold) if 0 in line else False,
        first_character_foreground=line[0].fg if 0 in line else "default",
    )


def _parse_prompt(line: _ScreenLine) -> tuple[bool, str | None]:
    # Autocomplete help prints prompt-shaped examples in cyan. The real zsh
    # prompt in these recordings is bold; retaining the style avoids treating
    # documentation output as another command.
    if not line.first_character_bold and (
        line.text.startswith("➜") or line.first_character_foreground == "cyan"
    ):
        return False, None
    for pattern in _PROMPTS:
        match = pattern.fullmatch(line.text)
        if match is not None:
            command = match.group("command").strip()
            if command == "exit" or _COMMAND_PREFIX.match(command) is None:
                return True, None
            return True, command
    is_empty = any(pattern.fullmatch(line.text) is not None for pattern in _EMPTY_PROMPTS)
    return is_empty, None


def _append_snippet(snippets: list[CastSnippet], command: str | None, output: list[str]) -> None:
    if command is None:
        return
    while output and not output[0]:
        output.pop(0)
    while output and not output[-1]:
        output.pop()
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(output)).strip()
    snippets.append(CastSnippet(command=command, result=result))
