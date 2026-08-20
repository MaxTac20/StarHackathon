from dataclasses import dataclass

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.transactions import Merchant, MerchantCategory, PaymentSession, PaymentTry, Terminal
from app.schemas.auth import MerchantCategorySummary
from app.schemas.merchants import (
    MerchantListResponse,
    MerchantSort,
    MerchantSummary,
    SortDirection,
)


@dataclass(frozen=True)
class MerchantListParams:
    search: str | None
    category_id: str | None
    sort: MerchantSort
    direction: SortDirection
    page: int
    page_size: int


def _merchant_filters(params: MerchantListParams) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []
    if params.search:
        escaped = (
            params.search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        if escaped:
            filters.append(Merchant.merchant_key.ilike(f"%{escaped}%", escape="\\"))
    if params.category_id:
        filters.append(Merchant.sessions.any(PaymentSession.category_id == params.category_id))
    return filters


async def list_merchants(session: AsyncSession, params: MerchantListParams) -> MerchantListResponse:
    filters = _merchant_filters(params)
    session_stats = (
        select(
            PaymentSession.merchant_id.label("merchant_id"),
            func.count(PaymentSession.id).label("session_count"),
            func.min(PaymentSession.created_at).label("first_session_at"),
            func.max(PaymentSession.created_at).label("latest_session_at"),
        )
        .group_by(PaymentSession.merchant_id)
        .subquery()
    )
    attempt_stats = (
        select(
            PaymentTry.merchant_id.label("merchant_id"),
            func.count(PaymentTry.id).filter(PaymentTry.try_seq >= 1).label("attempt_count"),
        )
        .group_by(PaymentTry.merchant_id)
        .subquery()
    )
    terminal_stats = (
        select(
            Terminal.merchant_id.label("merchant_id"),
            func.count(Terminal.id).label("terminal_count"),
        )
        .group_by(Terminal.merchant_id)
        .subquery()
    )

    columns = {
        MerchantSort.merchant_key: Merchant.merchant_key,
        MerchantSort.session_count: func.coalesce(session_stats.c.session_count, 0),
        MerchantSort.attempt_count: func.coalesce(attempt_stats.c.attempt_count, 0),
        MerchantSort.terminal_count: func.coalesce(terminal_stats.c.terminal_count, 0),
        MerchantSort.latest_activity: session_stats.c.latest_session_at,
    }
    sort_column = columns[params.sort]
    ordering = (
        asc(sort_column).nulls_last()
        if params.direction == SortDirection.asc
        else desc(sort_column).nulls_last()
    )

    statement: Select[tuple[object, ...]] = (
        select(
            Merchant.id,
            Merchant.merchant_key,
            func.coalesce(session_stats.c.session_count, 0).label("session_count"),
            func.coalesce(attempt_stats.c.attempt_count, 0).label("attempt_count"),
            func.coalesce(terminal_stats.c.terminal_count, 0).label("terminal_count"),
            session_stats.c.first_session_at,
            session_stats.c.latest_session_at,
        )
        .outerjoin(session_stats, session_stats.c.merchant_id == Merchant.id)
        .outerjoin(attempt_stats, attempt_stats.c.merchant_id == Merchant.id)
        .outerjoin(terminal_stats, terminal_stats.c.merchant_id == Merchant.id)
        .where(*filters)
        .order_by(ordering, Merchant.merchant_key.asc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    rows = (await session.execute(statement)).all()
    total_value = await session.scalar(select(func.count(Merchant.id)).where(*filters))
    total = int(total_value or 0)

    merchant_ids = [int(row.id) for row in rows]
    categories_by_merchant: dict[int, list[MerchantCategorySummary]] = {
        merchant_id: [] for merchant_id in merchant_ids
    }
    if merchant_ids:
        category_rows = (
            await session.execute(
                select(
                    PaymentSession.merchant_id,
                    MerchantCategory.category_id,
                    MerchantCategory.title_fa,
                )
                .join(MerchantCategory, MerchantCategory.category_id == PaymentSession.category_id)
                .where(PaymentSession.merchant_id.in_(merchant_ids))
                .distinct()
                .order_by(PaymentSession.merchant_id, MerchantCategory.category_id)
            )
        ).all()
        for row in category_rows:
            categories_by_merchant[int(row.merchant_id)].append(
                MerchantCategorySummary(category_id=row.category_id, title_fa=row.title_fa)
            )

    return MerchantListResponse(
        items=[
            MerchantSummary(
                merchant_key=row.merchant_key,
                categories=categories_by_merchant[int(row.id)],
                session_count=int(row.session_count),
                attempt_count=int(row.attempt_count),
                terminal_count=int(row.terminal_count),
                first_session_at=row.first_session_at,
                latest_session_at=row.latest_session_at,
            )
            for row in rows
        ],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
