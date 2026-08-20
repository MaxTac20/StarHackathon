from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import CurrentMerchant, DatabaseSession
from app.schemas.analytics import (
    MetricRegistryResponse,
    SortDirection,
    TransactionDetail,
    TransactionFilters,
    TransactionListResponse,
    TransactionSort,
)
from app.services.analytics import get_transaction, list_transactions, metric_registry

router = APIRouter(tags=["analytics"])


@router.get("/transactions", response_model=TransactionListResponse)
async def transactions(
    merchant: CurrentMerchant,
    session: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
    terminal_key: Annotated[str | None, Query(max_length=128)] = None,
    status: Annotated[str | None, Query(max_length=16)] = None,
    no_attempt: bool | None = None,
    psp: Annotated[str | None, Query(max_length=64)] = None,
    attempt_status: Annotated[str | None, Query(max_length=16)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    sort: TransactionSort = TransactionSort.created_at,
    direction: SortDirection = SortDirection.desc,
) -> TransactionListResponse:
    return await list_transactions(
        session,
        merchant,
        TransactionFilters(
            start=start,
            end=end,
            terminal_key=terminal_key,
            status=status,
            no_attempt=no_attempt,
            psp=psp,
            attempt_status=attempt_status,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        ),
    )


@router.get("/transactions/{session_key}", response_model=TransactionDetail)
async def transaction_detail(
    session_key: Annotated[str, Path(min_length=1, max_length=128)],
    merchant: CurrentMerchant,
    session: DatabaseSession,
) -> TransactionDetail:
    return await get_transaction(session, merchant, session_key)


@router.get("/metrics", response_model=MetricRegistryResponse)
async def metrics(_merchant: CurrentMerchant) -> MetricRegistryResponse:
    return metric_registry()
