from collections.abc import AsyncIterator
from typing import Any

from httpx import AsyncClient

from app.db.session import get_db
from app.main import app


async def inert_database() -> AsyncIterator[Any]:
    yield None


async def test_analytics_endpoints_require_authentication(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = inert_database
    for path in (
        "/api/dashboard/overview",
        "/api/dashboard/benchmarks",
        "/api/transactions",
        "/api/transactions/session-1",
        "/api/metrics",
    ):
        response = await client.get(path)
        assert response.status_code == 401


async def test_analytics_endpoints_require_selected_merchant(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = inert_database
    login = await client.post("/api/auth/login", json={"password": "CHANGE_ME"})
    assert login.status_code == 200
    response = await client.get("/api/dashboard/overview")
    assert response.status_code == 409
