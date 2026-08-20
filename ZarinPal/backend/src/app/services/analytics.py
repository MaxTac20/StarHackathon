from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from math import ceil, floor
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import case, desc, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Subquery

from app.models.transactions import (
    Merchant,
    MerchantCategory,
    PaymentSession,
    PaymentTry,
    Terminal,
)
from app.schemas.analytics import (
    AnalyticsScope,
    AttemptDetail,
    BenchmarkMetric,
    BenchmarkResponse,
    DailyStatus,
    DashboardOverview,
    FailureContribution,
    InsightEvidence,
    LatencyBucket,
    MetricContract,
    MetricRegistryResponse,
    MetricValue,
    PspOutcome,
    TransactionDetail,
    TransactionFilters,
    TransactionListResponse,
    TransactionSummary,
)

TIMEZONE = "Asia/Tehran"
METRIC_VERSION = "1.0.0"
STATUS_LIMITATION = "Verified and Paid are a proposed success composite; Reversed is separate."
TIME_LIMITATION = "Naive source timestamps are assumed to represent Asia/Tehran."


@dataclass(frozen=True)
class Range:
    start: datetime
    end: datetime
    previous_start: datetime
    previous_end: datetime
    latest: datetime


@dataclass(frozen=True)
class Aggregate:
    sessions: int
    amount: int
    fee: int
    failed: int
    success: int
    no_attempt: int
    attempted: int
    retry: int
    no_attempt_amount: int
    failed_no_attempt: int
    failed_no_attempt_amount: int


def safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = floor(position), ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def no_attempt_signal(
    current_count: int,
    current_total: int,
    previous_count: int,
    previous_total: int,
) -> tuple[float | None, float | None, float | None, int, bool]:
    current_rate = safe_rate(current_count, current_total)
    previous_rate = safe_rate(previous_count, previous_total)
    expected = current_total * previous_rate if previous_rate is not None else float(current_count)
    excess = max(0, round(current_count - expected))
    change_pp = (
        (current_rate - previous_rate) * 100
        if current_rate is not None and previous_rate is not None
        else None
    )
    alert = change_pp is not None and change_pp >= 5 and excess >= 20
    return current_rate, previous_rate, change_pp, excess, alert


async def resolve_range(
    session: AsyncSession,
    merchant_id: int,
    start: date | None,
    end: date | None,
) -> Range:
    latest = await session.scalar(
        select(func.max(PaymentSession.created_at)).where(PaymentSession.merchant_id == merchant_id)
    )
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No merchant data")
    canonical_end = datetime.combine(latest.date() + timedelta(days=1), time.min)
    end_dt = datetime.combine(end, time.min) if end else canonical_end
    start_dt = datetime.combine(start, time.min) if start else end_dt - timedelta(days=30)
    if start_dt >= end_dt:
        raise HTTPException(status_code=422, detail="start must be before end")
    if end_dt - start_dt > timedelta(days=366):
        raise HTTPException(status_code=422, detail="Date range cannot exceed 366 days")
    duration = end_dt - start_dt
    return Range(start_dt, end_dt, start_dt - duration, start_dt, latest)


def _scope(value: Range, terminal_key: str | None, refreshed_at: datetime) -> AnalyticsScope:
    return AnalyticsScope(
        start=value.start.date(),
        end=value.end.date(),
        previous_start=value.previous_start.date(),
        previous_end=value.previous_end.date(),
        terminal_key=terminal_key,
        refreshed_at=refreshed_at,
        latest_data_at=value.latest,
    )


def _attempt_stats_subquery(
    merchant_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    category_id: str | None = None,
) -> Subquery:
    statement = select(
        PaymentTry.session_id.label("session_id"),
        func.max(PaymentTry.try_seq).label("max_try_seq"),
        func.count(PaymentTry.id).filter(PaymentTry.try_seq >= 1).label("attempt_count"),
        func.max(case((PaymentTry.try_seq == 0, 1), else_=0)).label("no_attempt"),
    )
    if merchant_id is not None:
        statement = statement.where(PaymentTry.merchant_id == merchant_id)
    if start is not None or end is not None or category_id is not None:
        statement = statement.join(PaymentSession, PaymentSession.id == PaymentTry.session_id)
        if start is not None:
            statement = statement.where(PaymentSession.created_at >= start)
        if end is not None:
            statement = statement.where(PaymentSession.created_at < end)
        if category_id is not None:
            statement = statement.where(PaymentSession.category_id == category_id)
    return statement.group_by(PaymentTry.session_id).subquery()


async def _aggregates(
    session: AsyncSession,
    merchant_id: int,
    start: datetime,
    end: datetime,
    current_start: datetime,
    terminal_key: str | None,
) -> tuple[Aggregate, Aggregate]:
    attempt_stats = _attempt_stats_subquery(merchant_id, start, end)
    period = case((PaymentSession.created_at >= current_start, "current"), else_="previous").label(
        "period"
    )
    statement = (
        select(
            period,
            func.count(PaymentSession.id).label("sessions"),
            func.coalesce(func.sum(PaymentSession.amount), 0).label("amount"),
            func.coalesce(func.sum(PaymentSession.adjusted_fee), 0).label("fee"),
            func.count(PaymentSession.id)
            .filter(PaymentSession.session_status == "Failed")
            .label("failed"),
            func.count(PaymentSession.id)
            .filter(PaymentSession.session_status.in_(("Verified", "Paid")))
            .label("success"),
            func.count(PaymentSession.id)
            .filter(attempt_stats.c.no_attempt == 1)
            .label("no_attempt"),
            func.count(PaymentSession.id)
            .filter(attempt_stats.c.max_try_seq >= 1)
            .label("attempted"),
            func.count(PaymentSession.id).filter(attempt_stats.c.max_try_seq > 1).label("retry"),
            func.coalesce(
                func.sum(PaymentSession.amount).filter(attempt_stats.c.no_attempt == 1), 0
            ).label("no_attempt_amount"),
            func.count(PaymentSession.id)
            .filter((attempt_stats.c.no_attempt == 1) & (PaymentSession.session_status == "Failed"))
            .label("failed_no_attempt"),
            func.coalesce(
                func.sum(PaymentSession.amount).filter(
                    (attempt_stats.c.no_attempt == 1) & (PaymentSession.session_status == "Failed")
                ),
                0,
            ).label("failed_no_attempt_amount"),
        )
        .outerjoin(attempt_stats, attempt_stats.c.session_id == PaymentSession.id)
        .where(
            PaymentSession.merchant_id == merchant_id,
            PaymentSession.created_at >= start,
            PaymentSession.created_at < end,
        )
        .group_by(period)
    )
    if terminal_key:
        statement = statement.join(Terminal).where(Terminal.terminal_key == terminal_key)
    rows = (await session.execute(statement)).all()
    empty = Aggregate(*([0] * 11))
    aggregates = {
        row.period: Aggregate(
            *(int(row._mapping[field] or 0) for field in Aggregate.__annotations__)
        )
        for row in rows
    }
    return aggregates.get("current", empty), aggregates.get("previous", empty)


def _metric(
    metric_id: str,
    grain: str,
    value: int | float | None,
    previous: int | float | None,
    sample_size: int,
    numerator: int | None = None,
    denominator: int | None = None,
    limitations: list[str] | None = None,
) -> MetricValue:
    change = None if value is None or previous is None else value - previous
    return MetricValue(
        metric_id=metric_id,
        grain=grain,
        value=value,
        previous_value=previous,
        change=change,
        numerator=numerator,
        denominator=denominator,
        sample_size=sample_size,
        limitations=limitations or [],
    )


async def get_overview(
    session: AsyncSession,
    merchant: Merchant,
    start: date | None,
    end: date | None,
    terminal_key: str | None,
) -> DashboardOverview:
    range_value = await resolve_range(session, merchant.id, start, end)
    if terminal_key:
        valid_terminal = await session.scalar(
            select(Terminal.id).where(
                Terminal.merchant_id == merchant.id, Terminal.terminal_key == terminal_key
            )
        )
        if valid_terminal is None:
            raise HTTPException(status_code=404, detail="Terminal not found")

    current, previous = await _aggregates(
        session,
        merchant.id,
        range_value.previous_start,
        range_value.end,
        range_value.start,
        terminal_key,
    )
    refreshed_at = datetime.now(UTC)
    terminal_rows = (
        await session.scalars(
            select(Terminal.terminal_key)
            .where(Terminal.merchant_id == merchant.id)
            .order_by(Terminal.terminal_key)
        )
    ).all()
    category = (
        await session.execute(
            select(MerchantCategory.category_id, MerchantCategory.title_fa)
            .join(PaymentSession)
            .where(PaymentSession.merchant_id == merchant.id)
            .limit(1)
        )
    ).first()

    day_value = func.date(PaymentSession.created_at).label("day")
    daily_statement = (
        select(
            day_value,
            PaymentSession.session_status,
            func.count(PaymentSession.id).label("count"),
        )
        .where(
            PaymentSession.merchant_id == merchant.id,
            PaymentSession.created_at >= range_value.start,
            PaymentSession.created_at < range_value.end,
        )
        .group_by(day_value, PaymentSession.session_status)
        .order_by(day_value)
    )
    if terminal_key:
        daily_statement = daily_statement.join(Terminal).where(
            Terminal.terminal_key == terminal_key
        )
    daily_rows = (await session.execute(daily_statement)).all()
    by_day: dict[date, dict[str, int]] = {}
    for row in daily_rows:
        by_day.setdefault(row.day, {})[row.session_status] = int(row._mapping["count"])
    daily = [DailyStatus(day=day, **counts) for day, counts in by_day.items()]

    try_filters = [
        PaymentTry.merchant_id == merchant.id,
        PaymentSession.created_at >= range_value.previous_start,
        PaymentSession.created_at < range_value.end,
        PaymentTry.try_seq >= 1,
    ]
    try_period = case(
        (PaymentSession.created_at >= range_value.start, "current"), else_="previous"
    ).label("period")
    psp_statement = (
        select(
            try_period,
            PaymentTry.psp_code,
            func.count(PaymentTry.id).label("sample_size"),
            *[
                func.count(PaymentTry.id)
                .filter(PaymentTry.try_status == value)
                .label(value.lower() if value != "InBank" else "in_bank")
                for value in ("Failed", "Verified", "Paid", "Reversed", "InBank")
            ],
            func.count(PaymentTry.init_time_ms).label("latency_sample"),
            func.percentile_cont(0.5).within_group(PaymentTry.init_time_ms).label("median"),
            func.percentile_cont(0.95).within_group(PaymentTry.init_time_ms).label("p95"),
        )
        .join(PaymentSession, PaymentSession.id == PaymentTry.session_id)
        .where(*try_filters)
        .group_by(try_period, PaymentTry.psp_code)
        .order_by(try_period, desc("sample_size"))
    )
    if terminal_key:
        psp_statement = psp_statement.join(Terminal).where(Terminal.terminal_key == terminal_key)
    performance_rows = (await session.execute(psp_statement)).all()
    current_performance = [row for row in performance_rows if row.period == "current"]
    previous_latency = {row.psp_code: row for row in performance_rows if row.period == "previous"}
    latency = [
        LatencyBucket(
            psp_code=row.psp_code,
            sample_size=int(row.latency_sample),
            missing_count=int(row.sample_size - row.latency_sample),
            init_median_ms=float(row.median) if row.median is not None else None,
            init_p95_ms=float(row.p95) if row.p95 is not None else None,
            previous_init_median_ms=(
                float(previous_latency[row.psp_code].median)
                if row.psp_code in previous_latency
                and previous_latency[row.psp_code].median is not None
                else None
            ),
            previous_init_p95_ms=(
                float(previous_latency[row.psp_code].p95)
                if row.psp_code in previous_latency
                and previous_latency[row.psp_code].p95 is not None
                else None
            ),
        )
        for row in current_performance
    ]

    (
        current_no_attempt_rate,
        previous_no_attempt_rate,
        change_pp,
        excess,
        alert,
    ) = no_attempt_signal(
        current.no_attempt,
        current.sessions,
        previous.no_attempt,
        previous.sessions,
    )
    insight = InsightEvidence(
        kind="no_attempt_increase" if alert else "no_attempt_summary",
        severity="warning" if alert else "neutral",
        current_rate=current_no_attempt_rate,
        previous_rate=previous_no_attempt_rate,
        change_percentage_points=change_pp,
        excess_sessions=excess,
        affected_amount=current.failed_no_attempt_amount,
        drilldown_query="no_attempt=true&status=Failed",
        limitations=[TIME_LIMITATION, "Requested amount is exposure, not proven lost revenue."],
    )

    metrics = [
        _metric(
            "sessions.created", "session", current.sessions, previous.sessions, current.sessions
        ),
        _metric("amount.requested", "session", current.amount, previous.amount, current.sessions),
        _metric(
            "sessions.failed_rate",
            "session",
            safe_rate(current.failed, current.sessions),
            safe_rate(previous.failed, previous.sessions),
            current.sessions,
            current.failed,
            current.sessions,
        ),
        _metric(
            "sessions.verified_rate",
            "session",
            safe_rate(current.success, current.sessions),
            safe_rate(previous.success, previous.sessions),
            current.sessions,
            current.success,
            current.sessions,
            [STATUS_LIMITATION],
        ),
        _metric(
            "sessions.no_attempt_rate",
            "session",
            current_no_attempt_rate,
            previous_no_attempt_rate,
            current.sessions,
            current.no_attempt,
            current.sessions,
        ),
        _metric(
            "sessions.retry_rate",
            "session",
            safe_rate(current.retry, current.attempted),
            safe_rate(previous.retry, previous.attempted),
            current.attempted,
            current.retry,
            current.attempted,
        ),
        _metric(
            "fees.adjusted",
            "session",
            current.fee,
            previous.fee,
            current.sessions,
            limitations=["Recorded total; charging semantics are unconfirmed."],
        ),
    ]
    return DashboardOverview(
        merchant_key=merchant.merchant_key,
        category_id=category.category_id if category else None,
        category_title_fa=category.title_fa if category else None,
        terminals=list(terminal_rows),
        scope=_scope(range_value, terminal_key, refreshed_at),
        metrics=metrics,
        daily_status=daily,
        failure_contribution=FailureContribution(
            no_attempt=current.failed_no_attempt,
            attempted=max(0, current.failed - current.failed_no_attempt),
            total_failed=current.failed,
        ),
        psp_outcomes=[
            PspOutcome(
                psp_code=row.psp_code,
                sample_size=int(row.sample_size),
                failed=int(row.failed),
                verified=int(row.verified),
                paid=int(row.paid),
                reversed=int(row.reversed),
                in_bank=int(row.in_bank),
            )
            for row in current_performance
        ],
        latency=latency,
        insight=insight,
    )


async def get_benchmarks(
    session: AsyncSession,
    merchant: Merchant,
    start: date | None,
    end: date | None,
    terminal_key: str | None,
) -> BenchmarkResponse:
    range_value = await resolve_range(session, merchant.id, start, end)
    scope = _scope(range_value, terminal_key, datetime.now(UTC))
    category_id = await session.scalar(
        select(PaymentSession.category_id).where(PaymentSession.merchant_id == merchant.id).limit(1)
    )
    if terminal_key:
        return BenchmarkResponse(
            suppressed=True,
            suppression_reason="terminal_filter",
            category_id=category_id,
            scope=scope,
            metrics=[],
        )
    attempt_stats = _attempt_stats_subquery(
        start=range_value.start, end=range_value.end, category_id=category_id
    )
    rows = (
        await session.execute(
            select(
                PaymentSession.merchant_id,
                func.count(PaymentSession.id).label("sessions"),
                func.count(PaymentSession.id)
                .filter(PaymentSession.session_status == "Failed")
                .label("failed"),
                func.count(PaymentSession.id)
                .filter(PaymentSession.session_status.in_(("Verified", "Paid")))
                .label("success"),
                func.count(PaymentSession.id)
                .filter(attempt_stats.c.no_attempt == 1)
                .label("no_attempt"),
                func.count(PaymentSession.id)
                .filter(attempt_stats.c.max_try_seq >= 1)
                .label("attempted"),
                func.count(PaymentSession.id)
                .filter(attempt_stats.c.max_try_seq > 1)
                .label("retry"),
            )
            .outerjoin(attempt_stats, attempt_stats.c.session_id == PaymentSession.id)
            .where(
                PaymentSession.category_id == category_id,
                PaymentSession.created_at >= range_value.start,
                PaymentSession.created_at < range_value.end,
            )
            .group_by(PaymentSession.merchant_id)
            .having(func.count(PaymentSession.id) >= 30)
        )
    ).all()
    values: dict[int, dict[str, float]] = {}
    for row in rows:
        values[int(row.merchant_id)] = {
            "sessions.failed_rate": float(row.failed / row.sessions),
            "sessions.no_attempt_rate": float(row.no_attempt / row.sessions),
            "sessions.retry_rate": float(row.retry / row.attempted) if row.attempted else 0.0,
            "sessions.verified_rate": float(row.success / row.sessions),
        }
    latency_rows = (
        await session.execute(
            select(
                PaymentSession.merchant_id,
                func.percentile_cont(0.95).within_group(PaymentTry.init_time_ms).label("init_p95"),
            )
            .join(PaymentTry, PaymentTry.session_id == PaymentSession.id)
            .where(
                PaymentSession.category_id == category_id,
                PaymentSession.created_at >= range_value.start,
                PaymentSession.created_at < range_value.end,
                PaymentTry.try_seq >= 1,
                PaymentTry.init_time_ms.is_not(None),
            )
            .group_by(PaymentSession.merchant_id)
        )
    ).all()
    for row in latency_rows:
        merchant_values = values.get(int(row.merchant_id))
        if merchant_values is not None and row.init_p95 is not None:
            merchant_values["latency.init_p95"] = float(row.init_p95)
    peers = {key: value for key, value in values.items() if key != merchant.id}
    selected = values.get(merchant.id)
    if selected is None or len(peers) < 10:
        return BenchmarkResponse(
            suppressed=True,
            suppression_reason="insufficient_cohort",
            category_id=category_id,
            scope=scope,
            metrics=[],
        )
    directions = {
        "sessions.failed_rate": "lower",
        "sessions.no_attempt_rate": "lower",
        "sessions.retry_rate": "lower",
        "sessions.verified_rate": "higher",
        "latency.init_p95": "lower",
    }
    metrics: list[BenchmarkMetric] = []
    outside_iqr = False
    for metric_id, direction in directions.items():
        peer_values = [value[metric_id] for value in peers.values() if metric_id in value]
        chosen = selected.get(metric_id)
        if chosen is None or len(peer_values) < 10:
            continue
        q1, median, q3 = (percentile(peer_values, fraction) for fraction in (0.25, 0.5, 0.75))
        assert q1 is not None and median is not None and q3 is not None
        favorable = sum(
            peer >= chosen if direction == "lower" else peer <= chosen for peer in peer_values
        )
        if (direction == "lower" and chosen > q3) or (direction == "higher" and chosen < q1):
            outside_iqr = True
        metrics.append(
            BenchmarkMetric(
                metric_id=metric_id,
                selected_value=chosen,
                median=median,
                q1=q1,
                q3=q3,
                percentile=favorable / len(peer_values),
                cohort_size=len(peer_values),
                direction=direction,
            )
        )
    return BenchmarkResponse(
        suppressed=False,
        category_id=category_id,
        scope=scope,
        metrics=metrics,
        signal="unfavorable_outside_iqr" if outside_iqr else "neutral",
    )


async def list_transactions(
    session: AsyncSession, merchant: Merchant, filters: TransactionFilters
) -> TransactionListResponse:
    range_value = await resolve_range(session, merchant.id, filters.start, filters.end)
    direct_no_attempt = filters.no_attempt is True
    attempt_stats = (
        None
        if direct_no_attempt
        else _attempt_stats_subquery(merchant.id, range_value.start, range_value.end)
    )
    conditions = [
        PaymentSession.merchant_id == merchant.id,
        PaymentSession.created_at >= range_value.start,
        PaymentSession.created_at < range_value.end,
    ]
    if filters.status:
        conditions.append(PaymentSession.session_status == filters.status)
    if filters.terminal_key:
        conditions.append(Terminal.terminal_key == filters.terminal_key)
    attempt_count_column: ColumnElement[Any]
    last_psp_column: ColumnElement[Any]
    no_attempt_column: ColumnElement[Any]
    if direct_no_attempt:
        conditions.extend(
            (
                PaymentTry.merchant_id == merchant.id,
                PaymentTry.try_seq == 0,
                PaymentTry.try_status == "NoAttempt",
            )
        )
    elif filters.no_attempt is False:
        assert attempt_stats is not None
        conditions.append(attempt_stats.c.max_try_seq >= 1)
    if filters.psp:
        conditions.append(PaymentSession.tries.any(PaymentTry.psp_code == filters.psp))
    if filters.attempt_status:
        conditions.append(PaymentSession.tries.any(PaymentTry.try_status == filters.attempt_status))
    order_column = {
        "created_at": PaymentSession.created_at,
        "amount": PaymentSession.amount,
        "session_status": PaymentSession.session_status,
    }[filters.sort.value]
    ordering = order_column.asc() if filters.direction.value == "asc" else order_column.desc()
    if direct_no_attempt:
        attempt_count_column = literal(0)
        last_psp_column = literal(None)
        no_attempt_column = literal(True)
    else:
        assert attempt_stats is not None
        attempt_count_column = func.coalesce(attempt_stats.c.attempt_count, 0)
        last_psp_column = (
            select(PaymentTry.psp_code)
            .where(
                PaymentTry.session_id == PaymentSession.id,
                PaymentTry.merchant_id == merchant.id,
                PaymentTry.try_seq >= 1,
            )
            .order_by(PaymentTry.try_seq.desc())
            .limit(1)
            .correlate(PaymentSession)
            .scalar_subquery()
        )
        no_attempt_column = func.coalesce(attempt_stats.c.no_attempt, 0) == 1
    statement = select(
        PaymentSession.session_key,
        PaymentSession.created_at,
        Terminal.terminal_key,
        PaymentSession.amount,
        PaymentSession.session_status,
        attempt_count_column.label("attempt_count"),
        last_psp_column.label("last_psp"),
        no_attempt_column.label("no_attempt"),
        func.count(PaymentSession.id).over().label("total_count"),
    ).join(Terminal, Terminal.id == PaymentSession.terminal_id)
    if direct_no_attempt:
        statement = statement.join(PaymentTry, PaymentTry.session_id == PaymentSession.id)
    else:
        assert attempt_stats is not None
        statement = statement.outerjoin(
            attempt_stats, attempt_stats.c.session_id == PaymentSession.id
        )
    statement = statement.where(*conditions)
    rows = (
        await session.execute(
            statement.order_by(ordering, PaymentSession.session_key)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
    ).all()
    return TransactionListResponse(
        items=[TransactionSummary.model_validate(row._mapping) for row in rows],
        total=int(rows[0].total_count) if rows else 0,
        page=filters.page,
        page_size=filters.page_size,
        scope=_scope(range_value, filters.terminal_key, datetime.now(UTC)),
    )


async def get_transaction(
    session: AsyncSession, merchant: Merchant, session_key: str
) -> TransactionDetail:
    payment = await session.scalar(
        select(PaymentSession).where(
            PaymentSession.merchant_id == merchant.id,
            PaymentSession.session_key == session_key,
        )
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment session not found")
    terminal_key = await session.scalar(
        select(Terminal.terminal_key).where(Terminal.id == payment.terminal_id)
    )
    tries = (
        await session.scalars(
            select(PaymentTry)
            .where(PaymentTry.session_id == payment.id, PaymentTry.merchant_id == merchant.id)
            .order_by(PaymentTry.try_seq)
        )
    ).all()
    attempted = [item for item in tries if item.try_seq >= 1]
    return TransactionDetail(
        session=TransactionSummary(
            session_key=payment.session_key,
            created_at=payment.created_at,
            terminal_key=terminal_key or "",
            amount=payment.amount,
            session_status=payment.session_status,
            attempt_count=len(attempted),
            last_psp=attempted[-1].psp_code if attempted else None,
            no_attempt=not attempted,
        ),
        verify_type=payment.verify_type,
        adjusted_fee=payment.adjusted_fee,
        expires_at=payment.expires_at,
        attempts=[
            AttemptDetail(
                try_seq=item.try_seq,
                try_status=item.try_status,
                switch_response_code=item.switch_response_code,
                psp_code=item.psp_code,
                issuer_bank_code=item.issuer_bank_code,
                init_time_ms=item.init_time_ms,
                verify_time_ms=item.verify_time_ms,
                try_created_at=item.try_created_at,
                verified_at=item.verified_at,
                settled_at=item.settled_at,
            )
            for item in tries
        ],
    )


def metric_registry() -> MetricRegistryResponse:
    contracts = [
        ("sessions.created", "session", "count distinct session_key", False, []),
        ("amount.requested", "session", "sum amount once per session", False, []),
        ("sessions.failed_rate", "session", "Failed sessions / created sessions", False, []),
        (
            "sessions.verified_rate",
            "session",
            "Verified or Paid sessions / created sessions",
            True,
            [STATUS_LIMITATION],
        ),
        (
            "sessions.no_attempt_rate",
            "session",
            "sessions with no PSP attempt / created sessions",
            False,
            [],
        ),
        (
            "sessions.retry_rate",
            "session",
            "sessions with max try_seq > 1 / sessions with a PSP attempt",
            True,
            [],
        ),
        (
            "fees.adjusted",
            "session",
            "sum adjusted_fee once per session",
            True,
            ["Charging semantics are unconfirmed."],
        ),
        (
            "benchmarks.category_equal_weighted",
            "merchant",
            "median and IQR across eligible same-category merchants, one vote each",
            True,
            ["At least 30 sessions per peer and 10 peers are required."],
        ),
    ]
    return MetricRegistryResponse(
        version=METRIC_VERSION,
        metrics=[
            MetricContract(
                metric_id=metric_id,
                grain=grain,
                formula=formula,
                time_field="created_at",
                proposed=proposed,
                limitations=limitations + [TIME_LIMITATION],
            )
            for metric_id, grain, formula, proposed, limitations in contracts
        ],
    )
