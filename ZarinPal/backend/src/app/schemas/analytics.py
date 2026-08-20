from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    metric_id: str
    version: str = "1.0.0"
    grain: str
    value: float | int | None
    numerator: int | None = None
    denominator: int | None = None
    sample_size: int
    missing_count: int = 0
    previous_value: float | int | None = None
    change: float | int | None = None
    limitations: list[str] = Field(default_factory=list)


class AnalyticsScope(BaseModel):
    start: date
    end: date
    previous_start: date
    previous_end: date
    terminal_key: str | None = None
    time_field: str = "created_at"
    timezone: str = "Asia/Tehran"
    interval: str = "half-open"
    refreshed_at: datetime
    latest_data_at: datetime


class DailyStatus(BaseModel):
    day: date
    Failed: int = 0
    Verified: int = 0
    Paid: int = 0
    Reversed: int = 0


class PspOutcome(BaseModel):
    psp_code: str | None
    sample_size: int
    failed: int
    verified: int
    paid: int
    reversed: int
    in_bank: int


class LatencyBucket(BaseModel):
    psp_code: str | None
    sample_size: int
    missing_count: int
    init_median_ms: float | None
    init_p95_ms: float | None
    previous_init_median_ms: float | None
    previous_init_p95_ms: float | None


class FailureContribution(BaseModel):
    no_attempt: int
    attempted: int
    total_failed: int


class InsightEvidence(BaseModel):
    kind: str
    severity: str
    current_rate: float | None
    previous_rate: float | None
    change_percentage_points: float | None
    excess_sessions: int
    affected_amount: int
    drilldown_query: str
    limitations: list[str]


class DashboardOverview(BaseModel):
    merchant_key: str
    category_id: str | None
    category_title_fa: str | None
    terminals: list[str]
    scope: AnalyticsScope
    metrics: list[MetricValue]
    daily_status: list[DailyStatus]
    failure_contribution: FailureContribution
    psp_outcomes: list[PspOutcome]
    latency: list[LatencyBucket]
    insight: InsightEvidence


class BenchmarkMetric(BaseModel):
    metric_id: str
    selected_value: float | None
    median: float | None
    q1: float | None
    q3: float | None
    percentile: float | None
    cohort_size: int
    direction: str


class BenchmarkResponse(BaseModel):
    suppressed: bool
    suppression_reason: str | None = None
    category_id: str | None
    min_peer_observations: int = 30
    min_cohort_size: int = 10
    scope: AnalyticsScope
    metrics: list[BenchmarkMetric]
    signal: str = "neutral"


class TransactionSort(StrEnum):
    created_at = "created_at"
    amount = "amount"
    session_status = "session_status"


class SortDirection(StrEnum):
    asc = "asc"
    desc = "desc"


class TransactionSummary(BaseModel):
    session_key: str
    created_at: datetime
    terminal_key: str
    amount: int
    session_status: str
    attempt_count: int
    last_psp: str | None
    no_attempt: bool


class TransactionListResponse(BaseModel):
    items: list[TransactionSummary]
    total: int
    page: int
    page_size: int
    scope: AnalyticsScope


class AttemptDetail(BaseModel):
    try_seq: int
    try_status: str
    switch_response_code: str | None
    psp_code: str | None
    issuer_bank_code: str | None
    init_time_ms: int | None
    verify_time_ms: int | None
    try_created_at: datetime | None
    verified_at: datetime | None
    settled_at: datetime | None


class TransactionDetail(BaseModel):
    session: TransactionSummary
    verify_type: str
    adjusted_fee: int
    expires_at: datetime
    attempts: list[AttemptDetail]


class MetricContract(BaseModel):
    metric_id: str
    version: str = "1.0.0"
    grain: str
    formula: str
    time_field: str
    proposed: bool = False
    limitations: list[str] = Field(default_factory=list)


class MetricRegistryResponse(BaseModel):
    version: str
    metrics: list[MetricContract]


class TransactionFilters(BaseModel):
    start: date | None = None
    end: date | None = None
    terminal_key: str | None = None
    status: str | None = None
    no_attempt: bool | None = None
    psp: str | None = None
    attempt_status: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort: TransactionSort = TransactionSort.created_at
    direction: SortDirection = SortDirection.desc
