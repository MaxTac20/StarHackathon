import re

REDACTED_CREDENTIAL = "<REDACTED_CREDENTIAL>"
REDACTED_LINK = "<REDACTED_LINK>"

_RAW_URL_RE = re.compile(r"(?i)\bhttps?://[^\s<>()\]]+")
_CONNECTION_URI_RE = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqps?)://[^\s<>()]+"
)
_KEY_RE = re.compile(r"\b(?:sk|or)-[A-Za-z0-9_-]{12,}\b")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|"
    r"password|passwd|secret)\s*[:=]\s*(?!<REDACTED_CREDENTIAL>)[^\s,;]+"
)
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact_credentials(text: str) -> str:
    """Remove credential-shaped values without logging or inspecting their contents."""

    redacted = _PRIVATE_KEY_RE.sub(REDACTED_CREDENTIAL, text)
    redacted = _CONNECTION_URI_RE.sub(REDACTED_CREDENTIAL, redacted)
    redacted = _KEY_RE.sub(REDACTED_CREDENTIAL, redacted)
    redacted = _JWT_RE.sub(REDACTED_CREDENTIAL, redacted)

    def redact_assignment(match: re.Match[str]) -> str:
        return f"{match.group(1)}={REDACTED_CREDENTIAL}"

    return _SECRET_ASSIGNMENT_RE.sub(redact_assignment, redacted)


def sanitize_grounding_text(text: str) -> str:
    """Keep provider context useful while withholding links and credential shapes."""

    return _RAW_URL_RE.sub(REDACTED_LINK, redact_credentials(text))


def contains_raw_link(text: str) -> bool:
    return _RAW_URL_RE.search(text) is not None
