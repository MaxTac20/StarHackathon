from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

PLACEHOLDER = "<REDACTED_CREDENTIAL>"

_PASSWORD_FLAG = re.compile(
    r"(?<!\S)(?P<prefix>--password(?:=|\s+))(?P<value>\"[^\"]*\"|'[^']*'|\S+)",
    re.IGNORECASE,
)
_URI_CREDENTIAL = re.compile(
    r"(?P<prefix>\b[a-z][a-z0-9+.-]*://[^\s/:@]+:)(?P<value>[^@\s/]+)(?P<suffix>@)",
    re.IGNORECASE,
)
_PASSWORD_ASSIGNMENT = re.compile(
    r"""(?P<prefix>(?<![-\w])["']?(?:password|passwd|pwd)["']?\s*=(?!=|>)\s*)"""
    r"""(?P<value>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^;,\s}\]]+)""",
    re.IGNORECASE,
)
_PASSWORD_POSITION = re.compile(
    r"""(?P<prefix>(?<![-\w])["']?(?:password|passwd|pwd|pass|"""
    r"""[A-Za-z_][A-Za-z0-9_-]*(?:password|passwd|pwd|pass))["']?"""
    r"""\s*(?:=|:(?!=))\s*)"""
    r"""(?P<value>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^;,\s}\]]+)""",
    re.IGNORECASE,
)
_JWT = re.compile(
    r"(?<![A-Za-z0-9_-])(?P<value>eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)"
    r"(?![A-Za-z0-9_-])"
)
_SECRET_HEX = re.compile(
    r"""(?P<prefix>(?<![-\w])["']?secret(?:[_-]?key)?["']?(?:\s*[:=]\s*|\s+))"""
    r"""(?P<value>"[A-Fa-f0-9]{40,}"|'[A-Fa-f0-9]{40,}'|[A-Fa-f0-9]{40,})""",
    re.IGNORECASE,
)
_HIGH_ENTROPY = re.compile(
    r"(?<![A-Za-z0-9_+/.-])(?P<value>[A-Za-z0-9_+-]{24,}={0,2})(?![A-Za-z0-9_+/.-])"
)
_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_ALPHANUMERIC = re.compile(r"[A-Za-z0-9]{24,}")

_MYSQL_TOOLS = re.compile(r"(?:^|\s)(?:mysql|mariadb|mysqldump|mongo|mongorestore)(?:\s|$)")
_REDIS_TOOL = re.compile(r"(?:^|\s)redis-cli(?:\s|$)")
_SQLCMD_TOOL = re.compile(r"(?:^|\s)sqlcmd(?:\s|$)")
_SHORT_P_ATTACHED = re.compile(r"(?<!\S)(?P<prefix>-p)(?P<value>[^\s=-]\S*)")
_SHORT_P_SEPARATE = re.compile(r"(?<!\S)(?P<prefix>-p(?:=|\s+))(?P<value>\S+)")
_REDIS_PASSWORD = re.compile(r"(?<!\S)(?P<prefix>-a(?:=|\s+))(?P<value>\S+)")
_SQLCMD_PASSWORD = re.compile(r"(?<!\S)(?P<prefix>-P(?:=|\s+))(?P<value>\S+)")


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts_by_shape: dict[str, int]

    @property
    def count(self) -> int:
        return sum(self.counts_by_shape.values())


def redact_credentials(text: str) -> RedactionResult:
    """Replace credential-shaped values while preserving their surrounding syntax."""
    lines: list[str] = []
    counts: Counter[str] = Counter()
    for line in text.split("\n"):
        redacted_line, line_counts = _redact_command_passwords(line)
        lines.append(redacted_line)
        counts.update(line_counts)
    redacted = "\n".join(lines)

    for pattern, shape in (
        (_PASSWORD_FLAG, "password_flag"),
        (_URI_CREDENTIAL, "uri_credential"),
    ):
        redacted, replacements = _redact_matches(pattern, redacted, shape)
        counts.update(replacements)

    redacted, replacements = _redact_matches(
        _PASSWORD_ASSIGNMENT,
        redacted,
        _password_value_shape,
        skip_safe_password_values=True,
    )
    counts.update(replacements)

    redacted, replacements = _redact_matches(
        _PASSWORD_POSITION,
        redacted,
        _password_value_shape,
        skip_safe_password_values=True,
        value_filter=_looks_password_position_secret,
    )
    counts.update(replacements)

    for pattern, shape in ((_JWT, "jwt"), (_SECRET_HEX, "hex_secret")):
        redacted, replacements = _redact_matches(pattern, redacted, shape)
        counts.update(replacements)

    redacted, replacements = _redact_matches(
        _HIGH_ENTROPY,
        redacted,
        "high_entropy",
        value_filter=_looks_high_entropy,
    )
    counts.update(replacements)
    return RedactionResult(text=redacted, counts_by_shape=dict(sorted(counts.items())))


def _redact_command_passwords(line: str) -> tuple[str, Counter[str]]:
    patterns: tuple[re.Pattern[str], ...] = ()
    if _MYSQL_TOOLS.search(line):
        patterns = (_SHORT_P_SEPARATE, _SHORT_P_ATTACHED)
    elif _REDIS_TOOL.search(line):
        patterns = (_REDIS_PASSWORD,)
    elif _SQLCMD_TOOL.search(line):
        patterns = (_SQLCMD_PASSWORD,)

    counts: Counter[str] = Counter()
    for pattern in patterns:
        line, replacements = _redact_matches(pattern, line, "password_flag")
        counts.update(replacements)
    return line, counts


def _redact_matches(
    pattern: re.Pattern[str],
    text: str,
    shape: str | Callable[[str], str],
    *,
    skip_safe_password_values: bool = False,
    value_filter: Callable[[str], bool] | None = None,
) -> tuple[str, Counter[str]]:
    counts: Counter[str] = Counter()

    def replace(match: re.Match[str]) -> str:
        raw_value = match.group("value")
        value = _unquote(raw_value)
        if value == PLACEHOLDER:
            return match.group(0)
        if skip_safe_password_values and _is_safe_password_value(value):
            return match.group(0)
        if value_filter is not None and not value_filter(value):
            return match.group(0)
        shape_name = shape(value) if callable(shape) else shape
        counts[shape_name] += 1
        suffix = match.groupdict().get("suffix", "")
        quote = (
            raw_value[0]
            if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in "\"'"
            else ""
        )
        return f"{match.groupdict().get('prefix', '')}{quote}{PLACEHOLDER}{quote}{suffix}"

    return pattern.sub(replace, text), counts


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _is_safe_password_value(value: str) -> bool:
    folded = value.casefold()
    return (
        folded in {"password", "your-smtp-pass", "redispassword", "environment", "$uriparts"}
        or folded.startswith("environment.")
        or folded.startswith("$uriparts[")
    )


def _password_value_shape(value: str) -> str:
    if _UUID.fullmatch(value):
        return "password_uuid"
    if _looks_generated_password(value):
        return "password_alphanumeric"
    return "password_assignment"


def _looks_password_position_secret(value: str) -> bool:
    return _password_value_shape(value) != "password_assignment"


def _looks_high_entropy(value: str) -> bool:
    sample = value.rstrip("=")
    if len(sample) < 24:
        return False
    return _entropy(sample) >= 4.0 and _has_mixed_alphanumeric_categories(sample)


def _looks_generated_password(value: str) -> bool:
    return (
        len(value) >= 24
        and _ALPHANUMERIC.fullmatch(value) is not None
        and any(character.islower() for character in value)
        and any(character.isupper() for character in value)
        and _entropy(value) >= 3.8
    )


def _entropy(value: str) -> float:
    frequencies = Counter(value)
    return -sum(
        (frequency / len(value)) * math.log2(frequency / len(value))
        for frequency in frequencies.values()
    )


def _has_mixed_alphanumeric_categories(value: str) -> bool:
    return (
        any(character.islower() for character in value)
        and any(character.isupper() for character in value)
        and any(character.isdigit() for character in value)
    )
