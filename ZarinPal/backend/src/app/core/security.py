"""Small security helpers for the shared demo-access credential."""

from hmac import compare_digest

from pydantic import SecretStr


def password_matches(candidate: str, expected: SecretStr) -> bool:
    """Compare the configured demo password without timing-sensitive equality."""
    return compare_digest(candidate.encode(), expected.get_secret_value().encode())
