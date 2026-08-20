# Supplied transaction data

## Snapshot profile

This profile was generated from the local `data/challenge_data.csv` supplied for the
challenge. The files under `data/` are intentionally gitignored.

| Property | Observed value |
|---|---:|
| Data rows | 2,213,289 |
| Unique `session_key` values | 2,062,839 |
| Merchant keys | 343 |
| Terminal keys | 348 |
| Merchant-terminal pairs | 348 |
| Observed `created_at` range | 2026-01-01 00:00:08 through 2026-06-30 23:59:55 |
| PSP codes | 8 |
| Issuer-bank codes | 31 |
| Merchant categories | 5 |

The CSV is approximately 473 MiB and its gzip copy approximately 59 MiB. The profile is
a description of this snapshot, not a permanent product contract.

## Grain and relationships

Each row describes a payment try within a session. A `session_key` can occur more than
once, with `try_seq` ordering tries. There are 263,936 observed `try_seq = 0` rows; these
also have `try_status = NoAttempt` and no PSP/try timestamp. Most attempted sessions use
`try_seq = 1`, while retry sequences extend as high as 135 in this snapshot.

`merchant_key` scopes a merchant and `terminal_key` identifies its terminal. The observed
counts suggest most merchants have one terminal and a few have more, but authorization
must rely on an explicit merchant-terminal relationship rather than this observation.

## Column dictionary

Meanings below are either directly observable or conservative interpretations of field
names. Items marked “confirm” require source-system documentation. All monetary columns
in the supplied CSV are denominated in Iranian rials (`ریال`).

| Column | Observed shape | Working interpretation |
|---|---|---|
| `session_key` | Integer-like identifier | Payment-session identifier; deduplication key |
| `try_seq` | Integer, 0–135 | Ordered try number; `0` is observed for no-attempt sessions |
| `terminal_key` | Token such as `T318` | Merchant terminal identifier |
| `merchant_key` | Token such as `M145` | Merchant identifier and required data-isolation scope |
| `category_id` | 8-digit code | Merchant category identifier |
| `category_title` | Persian text | Merchant category display label |
| `amount` | Integer, 1,000–2,000,000,000 | Requested payment amount in Iranian rials (`ریال`) |
| `adjusted_fee` | Integer, 1,920–284,800 | Adjusted fee in Iranian rials (`ریال`); charging semantics must be confirmed |
| `session_status` | Enum-like text | Session outcome: `Failed`, `Verified`, `Paid`, or `Reversed` |
| `try_status` | Enum-like text | Try state: `NoAttempt`, `InBank`, `Failed`, `Verified`, `Paid`, or `Reversed` |
| `switch_response_code` | Usually `<PSP>:<code>` | PSP/switch response; code catalog and null meaning must be confirmed |
| `psp_code` | `PSP-01`…`PSP-08` | Payment service provider pseudonym |
| `issuer_bank_code` | `BANK-01`…`BANK-31` | Issuing-bank pseudonym |
| `payer_card_key` | Token such as `CARD-181237` | Tokenized payer-card identifier; treat as sensitive |
| `verify_type` | `Automated` or `Manual` | Verification mode |
| `init_time_ms` | Integer milliseconds, 44–59,905 | Initialization latency; exact boundaries must be confirmed |
| `verify_time_ms` | Integer milliseconds, 35–58,553 | Verification latency; exact boundaries must be confirmed |
| `created_at` | Naive datetime | Session creation time; timezone must be confirmed |
| `try_created_at` | Naive datetime | Try creation time |
| `verified_at` | Nullable naive datetime | Verification time |
| `settled_at` | Nullable naive datetime | Settlement time or signal; semantics must be confirmed |
| `expire_in` | Naive datetime despite its name | Observed expiry timestamp, not a duration; confirm source contract |

The five observed categories are internet service provider, computer network/internet
services, cosmetics/health products, virtual education, and bags/shoes. Preserve the
source Persian titles and provide curated English translations in the presentation
layer rather than altering source data.

## Missingness

Blank fields are meaningful and must not be converted to zero or a successful state.

| Column | Blank rows | Approximate share |
|---|---:|---:|
| `switch_response_code` | 2,155,696 | 97.4% |
| `issuer_bank_code` | 1,178,921 | 53.3% |
| `payer_card_key` | 1,178,921 | 53.3% |
| `verify_time_ms` | 1,179,013 | 53.3% |
| `verified_at` | 1,125,164 | 50.8% |
| `settled_at` | 1,116,034 | 50.4% |
| `psp_code` | 263,936 | 11.9% |
| `init_time_ms` | 346,747 | 15.7% |
| `try_created_at` | 263,936 | 11.9% |

Null patterns often reflect lifecycle state—for example, no-attempt rows lack a PSP—but
this must be encoded as tested domain logic, not blanket imputation.

## Ingestion safeguards

- Parse with explicit types and reject/quarantine malformed rows with a non-sensitive
  reason; never log full raw rows.
- Preserve raw identifiers as strings even when they look numeric.
- Validate session invariants such as stable merchant, terminal, amount, and session
  status across retries.
- Enforce uniqueness on the chosen row identity (provisionally `session_key + try_seq`)
  only after checking whether duplicate try sequences exist.
- Keep raw timestamp values until timezone semantics are confirmed.
- Record source filename/checksum, imported-at time, row counts, rejected rows, and
  transformation version for reproducibility.
- Index the merchant and time dimensions used by the dashboard, plus session lookup;
  verify index choices against real query plans after import.
