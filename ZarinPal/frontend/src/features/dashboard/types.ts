export interface AnalyticsScope {
  start: string;
  end: string;
  previous_start: string;
  previous_end: string;
  terminal_key: string | null;
  time_field: string;
  timezone: string;
  interval: string;
  refreshed_at: string;
  latest_data_at: string;
}

export interface MetricValue {
  metric_id: string;
  version: string;
  grain: string;
  value: number | null;
  numerator: number | null;
  denominator: number | null;
  sample_size: number;
  missing_count: number;
  previous_value: number | null;
  change: number | null;
  limitations: string[];
}

export interface DashboardOverview {
  merchant_key: string;
  category_id: string | null;
  category_title_fa: string | null;
  terminals: string[];
  scope: AnalyticsScope;
  metrics: MetricValue[];
  daily_status: Array<{
    day: string;
    Failed: number;
    Verified: number;
    Paid: number;
    Reversed: number;
  }>;
  failure_contribution: {
    no_attempt: number;
    attempted: number;
    total_failed: number;
  };
  psp_outcomes: Array<{
    psp_code: string | null;
    sample_size: number;
    failed: number;
    verified: number;
    paid: number;
    reversed: number;
    in_bank: number;
  }>;
  latency: Array<{
    psp_code: string | null;
    sample_size: number;
    missing_count: number;
    init_median_ms: number | null;
    init_p95_ms: number | null;
    previous_init_median_ms: number | null;
    previous_init_p95_ms: number | null;
  }>;
  insight: {
    kind: string;
    severity: string;
    current_rate: number | null;
    previous_rate: number | null;
    change_percentage_points: number | null;
    excess_sessions: number;
    affected_amount: number;
    drilldown_query: string;
    limitations: string[];
  };
}

export interface BenchmarkResponse {
  suppressed: boolean;
  suppression_reason: string | null;
  category_id: string | null;
  min_peer_observations: number;
  min_cohort_size: number;
  scope: AnalyticsScope;
  signal: string;
  metrics: Array<{
    metric_id: string;
    selected_value: number | null;
    median: number | null;
    q1: number | null;
    q3: number | null;
    percentile: number | null;
    cohort_size: number;
    direction: string;
  }>;
}

export interface TransactionSummary {
  session_key: string;
  created_at: string;
  terminal_key: string;
  amount: number;
  session_status: string;
  attempt_count: number;
  last_psp: string | null;
  no_attempt: boolean;
}

export interface TransactionListResponse {
  items: TransactionSummary[];
  total: number;
  page: number;
  page_size: number;
  scope: AnalyticsScope;
}

export interface TransactionDetail {
  session: TransactionSummary;
  verify_type: string;
  adjusted_fee: number;
  expires_at: string;
  attempts: Array<{
    try_seq: number;
    try_status: string;
    switch_response_code: string | null;
    psp_code: string | null;
    issuer_bank_code: string | null;
    init_time_ms: number | null;
    verify_time_ms: number | null;
    try_created_at: string | null;
    verified_at: string | null;
    settled_at: string | null;
  }>;
}
