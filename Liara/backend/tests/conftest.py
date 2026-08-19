from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app


async def unused_database() -> AsyncIterator[AsyncSession]:
    raise AssertionError("This test should not access the database")
    yield  # pragma: no cover


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_db] = unused_database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()
