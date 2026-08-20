from pydantic import SecretStr

from app.core.security import password_matches


def test_password_matches_configured_secret() -> None:
    password = SecretStr("CHANGE_ME")
    assert password_matches("CHANGE_ME", password)
    assert not password_matches("change_me", password)
