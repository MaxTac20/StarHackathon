from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app


async def dummy_database() -> AsyncIterator[AsyncSession]:
    yield AsyncMock(spec=AsyncSession)


async def test_login_sets_eight_hour_signed_session_cookie(client: AsyncClient) -> None:
    response = await client.post("/api/auth/login", json={"password": "CHANGE_ME"})

    assert response.status_code == 200
    assert response.json() == {"authenticated": True, "selected_merchant": None}
    cookie = response.headers["set-cookie"]
    assert "zarinpal_session=" in cookie
    assert "Max-Age=28800" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()
    assert "CHANGE_ME" not in cookie


async def test_invalid_password_is_rejected_without_setting_cookie(client: AsyncClient) -> None:
    response = await client.post("/api/auth/login", json={"password": "incorrect"})

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid password"
    assert "set-cookie" not in response.headers


async def test_session_round_trip_and_logout(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = dummy_database
    assert (await client.post("/api/auth/login", json={"password": "CHANGE_ME"})).is_success

    session = await client.get("/api/auth/session")
    assert session.json() == {"authenticated": True, "selected_merchant": None}

    logout = await client.post("/api/auth/logout")
    assert logout.status_code == 204
    assert (await client.get("/api/auth/session")).json() == {
        "authenticated": False,
        "selected_merchant": None,
    }
