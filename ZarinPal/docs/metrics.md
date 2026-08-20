# Metric contracts and traceability

This document is the initial analytics contract. Definitions marked **proposed** must be
validated with ZarinPal domain owners before being treated as canonical. The dataset
profile behind these proposals is in [data-dictionary.md](data-dictionary.md).

## Grain comes first

The CSV is attempt-grained: `session_key` repeats when a payment session is retried, and
`try_seq = 0` represents a `NoAttempt` row with no PSP. Therefore:

- **Session metrics** deduplicate by `session_key`.
- **Attempt metrics** count eligible rows/tries and say “attempt,” not “transaction.”
- Monetary session metrics must count a session amount or fee once, not once per retry.
- Attempt dimensions such as PSP and switch response code need an explicit attribution
  rule when rolled up to sessions (for example, last attempt or any attempt).

## Initial metric registry

| ID | Display metric | Grain | Proposed calculation | Important exclusions/notes |
|---|---|---|---|---|
| `sessions.created` | Payment sessions | Session | `count(distinct session_key)` created in range | Time basis: `created_at` |
| `attempts.processed` | PSP attempts | Attempt | Count rows where `try_seq >= 1` | Excludes `NoAttempt` rows |
| `amount.requested` | Requested amount | Session | Sum one `amount` per distinct session | Denominated in Iranian rials (`ریال`) |
| `sessions.verified_rate` | Verification rate | Session | Sessions with successful final verification / created sessions | **Proposed:** successful final statuses are `Verified` and `Paid`; confirm `Reversed` handling |
| `sessions.failed_rate` | Failure rate | Session | Sessions with final `session_status = Failed` / created sessions | Preserve no-attempt failures in denominator |
| `sessions.settled_rate` | Settlement rate | Session | Sessions with non-null `settled_at` / settlement-eligible sessions | Eligibility and reporting time basis need domain confirmation |
| `fees.adjusted` | Adjusted fees | Session | Sum one `adjusted_fee` per distinct eligible session | Denominated in Iranian rials (`ریال`); confirm whether failed/unsettled fees are charged and whether fee repeats per retry |
| `latency.init` | Initialization latency | Attempt | Median and p95 of non-null `init_time_ms` | Show sample count and missing rate |
| `latency.verify` | Verification latency | Attempt | Median and p95 of non-null `verify_time_ms` | Show sample count and missing rate |
| `sessions.retry_rate` | Retry rate | Session | Sessions whose maximum `try_seq > 1` / sessions with at least one PSP attempt | Excludes `NoAttempt`; confirm retry semantics |
| `failures.by_code` | Failure-code distribution | Attempt | Failed eligible attempts grouped by `switch_response_code` | Include unavailable code; display numerator and population |

“Final status” means the session-level value after applying a documented deterministic
selection rule. Current data appears to repeat `session_status` across a session's rows,
but ingestion should validate this invariant rather than depend on it silently.

## Required traceability UI

Each metric surface must provide an info affordance containing:

- localized name and plain-language meaning;
- formula, including numerator and denominator;
- whether it counts sessions or attempts;
- status mapping and null handling;
- active filters and comparison period;
- timestamp field and display timezone;
- data freshness and metric-definition version;
- numerator, denominator, and sample size where applicable;
- a “View transactions” action carrying the same reproducible filters.

Tables reached through drill-down must make the grain visible and let the user move
between a session and its ordered attempts. Downloads must reproduce the visible filter
scope and include a generated-at timestamp and metric version.

## Time and comparison rules

- Filter inclusion should be half-open: `[start, end)`.
- Store/query timestamps consistently and format only at the presentation boundary.
- Always name the time field used by a chart. Created, attempted, verified, and settled
  views are different populations.
- Period-over-period comparisons use the immediately preceding interval of equal length,
  in the same timezone, unless the UI states otherwise.
- Avoid a percentage-change value when the comparison denominator is zero; show it as
  unavailable with an explanation.

## Validation requirements

Backend tests should exercise duplicate attempts, no-attempt sessions, null dimensions,
boundary timestamps, each status, and division by zero. Reconcile aggregate totals to a
small fixture whose expected rows are human-auditable. API responses should include the
metric ID/version and enough metadata for the frontend explanation panel.

## Open domain questions

1. What timezone applies to the naive timestamps?
2. Which statuses constitute business success, and how should `Paid` and `Reversed` be
   handled?
3. Is `settled_at` the authoritative settlement signal, and which sessions are eligible?
4. Is `adjusted_fee` charged per session, per successful payment, or per try?
5. What exactly do `init_time_ms` and `verify_time_ms` measure?
6. Does `switch_response_code` encode `<psp>:<code>` in every valid non-null case, and is
   there an official response-code catalog?
