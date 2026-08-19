# 0004 — Name defective documentation pages, with evidence, below the answer

**Status:** accepted · 2026-08-20

## Context

Liara's documentation contains verified content errors that perfect retrieval serves
confidently. `dbaas/mongodb/how-tos/connect-via-platform/go.md` is byte-identical to the
PostgreSQL page — ask how to connect Go to MongoDB and the docs hand you GORM with
`gorm.io/driver/postgres`. The Redis/.NET page is titled "Redis in Flask apps".
`rabbitmq/create-user` is the MariaDB page. `paas/update.md` has its Console and CLI
headings swapped.

## Decision

**Answer from elsewhere, then name the defect below the answer, with evidence, keeping
the bad page in the citation list marked bad.**

Below the answer, because the user asked a question and deserves the answer first. With
specific, checkable evidence — the byte-identical hash, the offending import line, the
sentence with no code block after it — because an accusation this strong must be
verifiable.

## Rejected

- **Silent exclusion.** The choice most teams will make, and wrong. The broken page stays
  live and top-ranked in search. A user we quietly routed around finds it an hour later,
  ships GORM into a MongoDB service, and correctly blames us for having known and said
  nothing.
- **A vague "this source may be unreliable" banner.** Worse than silence —
  unfalsifiable, unactionable, and it teaches distrust of every source we cite.
- **Refusing to answer.** We can answer, and spurious refusal is a measured failure mode
  that users punish harder than visible hedging.

## Hard constraint

Only defect classes with a **near-zero false-positive rate** earn a user-visible
accusation: byte-identical pages across different services, title/content mismatch
confirmed by an import statement, "run the command below" with no fence following.

Soft signals — 0.5 Jaccard similarity, near-duplication — get **no accusation at all**.
They only downweight retrieval and feed the internal dashboard.

Publicly calling a correct page broken would be a trust catastrophe. That asymmetry, not
squeamishness, sets the bar.

## Why this is worth the design effort

It is the only point in the product where the assistant can be **demonstrably more
correct than its own source of truth**. Any RAG bot can quote the docs; only one that
knows where they are broken can beat them. The rubric penalizes incorrect answers — which
includes perfectly grounded answers copied from a wrong page.
