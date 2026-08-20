from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentMerchant, DatabaseSession
from app.schemas.analytics import BenchmarkResponse, DashboardOverview
from app.services.analytics import get_benchmarks, get_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def overview(
    merchant: CurrentMerchant,
    session: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
    terminal_key: Annotated[str | None, Query(max_length=128)] = None,
) -> DashboardOverview:
    return await get_overview(session, merchant, start, end, terminal_key)


@router.get("/benchmarks", response_model=BenchmarkResponse)
async def benchmarks(
    merchant: CurrentMerchant,
    session: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
    terminal_key: Annotated[str | None, Query(max_length=128)] = None,
) -> BenchmarkResponse:
    return await get_benchmarks(session, merchant, start, end, terminal_key)
