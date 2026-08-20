# Product brief

## Challenge

Payment-gateway merchants generate a large volume of transaction data, but raw records
are hard to interpret and provide little immediate business value. This product turns
the supplied ZarinPal transaction data into a merchant-specific analytics dashboard for
monitoring payment performance, finding recurring failures, and making operational
decisions.

## Audience and outcome

The primary user is a merchant operator, finance lead, or support analyst. After opening
the dashboard, they should be able to answer:

- How many payment sessions and payment attempts occurred, and what amount did they
  represent?
- What proportion succeeded, failed, settled, or required retries?
- How much fee was associated with the selected population?
- Where are failures concentrated by PSP, issuer bank, response code, terminal, or time?
- Has initialization or verification latency degraded?
- Which transactions contributed to a chart point or KPI, and how was that value
  calculated?

The dashboard is diagnostic, not merely descriptive: overview signals lead to a useful
breakdown and ultimately to the filtered contributing records.

## Product success lens

The challenge rewards actionable and original insights most heavily, followed by
accuracy and traceability, analytical depth, usability for non-technical merchants, and
technical quality. See [challenge-criteria.md](challenge-criteria.md) for the official
deliverables, score weighting, and submission-readiness checklist.

The default product unit is therefore an **insight journey**, not a chart. It begins
with a plain-language quantified finding, narrows the finding to the supported segment
or condition that contributes most, proposes a feasible next action, explains evidence
and limitations, and ends at the contributing sessions and attempts. Charts and KPIs
support that journey; they are not the outcome by themselves.

## Product principles

### Merchant isolation

Every query is scoped on the server to the current merchant. A client-supplied
`merchant_key` must never be treated as authorization. Cross-merchant views, if ever
needed, are a separately authorized internal product.

### Explainable analytics

Every KPI and derived chart series follows a named, versioned metric contract. The UI
shows a plain-language definition and exposes the numerator, denominator, time field,
timezone, active filters, last refresh time, and drill-down records. See
[metrics.md](metrics.md).

### Persian first, English complete

Persian (`fa`) is the default locale with an RTL document direction. English (`en`) is
a complete secondary locale with LTR direction. Navigation, chart labels, table states,
errors, validation, tooltips, accessibility names, and exported column labels all need
translations. Codes such as `PSP-05`, bank codes, masked cards, and transaction IDs stay
LTR inside either locale.

Dates, numbers, and currency use locale-aware formatting without changing stored values.
All monetary columns in the supplied CSV, including `amount` and `adjusted_fee`, are
denominated in Iranian rials (`ریال`). The timestamp timezone and whether Persian views
should default to the Solar Hijri calendar are product decisions still requiring
confirmation.

### Theme parity

Light and dark themes are equal product surfaces. Status meaning cannot rely on color
alone, and charts must retain contrast, hover states, focus states, and series
distinction in both themes.

## Initial information architecture

1. **Overview:** volume, amount, success/failure, fees, settlement, latency, and notable
   changes for the selected period.
2. **Failures:** trends and ranked breakdowns by try status, response code, PSP, issuer
   bank, terminal, and hour/day.
3. **Settlement and fees:** settled population, settlement timing, fee totals/rates, and
   exceptions.
4. **Performance:** initialization and verification latency distributions and trends.
5. **Transactions:** filterable drill-down records that preserve session/attempt grain.
6. **Metric guide:** searchable definitions and known data limitations.

Global filters should include time range and terminal; analysis pages add PSP, issuer
bank, status, response code, and verification type as appropriate. Filter state should
be shareable in the URL where it does not reveal sensitive information.

## Scope guardrails

- Do not call a row a unique transaction: one session can have multiple try rows.
- Do not equate a successful try, verified session, paid session, and settled session
  without an explicit metric contract.
- Do not expose full payer-card identifiers. Treat `payer_card_key` as sensitive even
  though it is tokenized in the supplied data.
- Do not present rankings on tiny populations without showing the sample size.
- Do not silently discard null PSP, issuer bank, response code, or latency values; show
  an Unknown/Unavailable bucket when analytically relevant.

## Definition of done for an analytics slice

A feature is complete when its server-side merchant scope, metric contract, Persian and
English copy, RTL/LTR behavior, light/dark presentation, loading/empty/error states,
drill-down path, and representative tests are all present. A primary insight feature
must additionally pass the feature review checklist in
[challenge-criteria.md](challenge-criteria.md), including quantified impact, an
appropriate comparison, a feasible action, visible limitations and null coverage, and
mobile/desktop demo readiness.
