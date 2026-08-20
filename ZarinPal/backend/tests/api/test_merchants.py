from collections.abc import AsyncIterator
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import auth as auth_routes
from app.api.routes import merchants as merchant_routes
from app.db.session import get_db
from app.main import app
from app.schemas.auth import MerchantCategorySummary, SelectedMerchant
from app.schemas.merchants import MerchantListResponse, MerchantSummary
from app.services.merchants import MerchantListParams


async def dummy_database() -> AsyncIterator[AsyncSession]:
    yield AsyncMock(spec=AsyncSession)


async def test_merchant_list_requires_demo_authentication(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = dummy_database
    response = await client.get("/api/merchants")
    assert response.status_code == 401


async def test_merchant_list_forwards_filter_sort_and_pagination(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    app.dependency_overrides[get_db] = dummy_database
    captured: MerchantListParams | None = None

    async def fake_list(_session: AsyncSession, params: MerchantListParams) -> MerchantListResponse:
        nonlocal captured
        captured = params
        return MerchantListResponse(
            items=[
                MerchantSummary(
                    merchant_key="M145",
                    categories=[
                        MerchantCategorySummary(
                            category_id="48160002", title_fa="ارائه دهنده خدمات اینترنت"
                        )
                    ],
                    session_count=42,
                    attempt_count=45,
                    terminal_count=1,
                    first_session_at=datetime(2026, 1, 1),
                    latest_session_at=datetime(2026, 6, 30),
                )
            ],
            total=1,
            page=2,
            page_size=10,
        )

    monkeypatch.setattr(merchant_routes, "list_merchants", fake_list)
    await client.post("/api/auth/login", json={"password": "CHANGE_ME"})
    response = await client.get(
        "/api/merchants?search=M14&category_id=48160002"
        "&sort=attempt_count&direction=asc&page=2&page_size=10"
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["session_count"] == 42
    assert captured is not None
    assert captured.search == "M14"
    assert captured.category_id == "48160002"
    assert captured.sort == "attempt_count"
    assert captured.direction == "asc"
    assert captured.page == 2


async def test_two_browsers_keep_independent_merchant_selections(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    app.dependency_overrides[get_db] = dummy_database

    async def fake_selected(_session: AsyncSession, merchant_key: str) -> SelectedMerchant:
        return SelectedMerchant(merchant_key=merchant_key, categories=[])

    monkeypatch.setattr(auth_routes, "get_selected_merchant", fake_selected)
    await client.post("/api/auth/login", json={"password": "CHANGE_ME"})
    response = await client.put("/api/auth/merchant", json={"merchant_key": "M145"})
    assert response.json()["selected_merchant"]["merchant_key"] == "M145"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://second-browser"
    ) as second_client:
        await second_client.post("/api/auth/login", json={"password": "CHANGE_ME"})
        second = await second_client.put("/api/auth/merchant", json={"merchant_key": "M200"})
        assert second.json()["selected_merchant"]["merchant_key"] == "M200"

    first = await client.get("/api/auth/session")
    assert first.json()["selected_merchant"]["merchant_key"] == "M145"
