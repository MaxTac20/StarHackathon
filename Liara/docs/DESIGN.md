# DESIGN

What we are building for the Liara challenge, and why. Requirements live in
[`../CHALLENGE.md`](../CHALLENGE.md); this file holds the design decisions made within
them. Current status is in [`STATE.md`](STATE.md).

---

## 1. The product in one paragraph

A bilingual assistant over Liara's documentation whose distinguishing capability is that
it **works from artifacts, not just questions**. Paste a failing build log, a crash
trace, or a `liara.json`, and it identifies the problem, returns the fix as a diff
against your own config, cites the doc page it came from, and gives you a command to
verify the fix worked. It also generates deployment artifacts for a described stack —
validated before you ever see them. Underneath both sits a grounding layer that makes
fabrication structurally difficult, and which knows where Liara's own documentation is
wrong.

## 2. Why this shape

The rubric is not shaped like a chatbot contest. Security, deployment and cost total
115 points (38%) and depend on engineering discipline rather than model cleverness. UI/UX
at 55 outranks agentic at 50. Answer quality at 80 is the largest single bucket.

So: **the cited-RAG chat is the substrate, not the product.** It carries the 80 answer
quality points and most of the 55 UI points regardless of what else we build. The
differentiation has to sit somewhere that also serves those buckets rather than competing
with them.

A survey of the docs-AI industry found the differentiators available:

- Shipping an MCP server or agent skills for the user's own coding agent is **table
  stakes, not differentiation** — Cloudflare, Microsoft, OpenAI, AWS, Mintlify, GitBook,
  Redocly, kapa, Algolia, Context7, Stripe and Railway all ship one. We should offer it
  because its absence looks dated. It wins us nothing.
- **Log-grounded diagnosis exists in four products** (Netlify, Vercel, Railway, Render)
  and every one is dashboard-bound, reading logs by service ID because the platform owns
  the deployment. Accepting a *pasted* log is unbuilt.
- **Config generation validated before being shown: nobody.** The only
  validation-in-the-loop found anywhere is Mintlify validating its own docs builds.
- **RTL is an open goal.** Claude Code, Cursor, Codex and Copilot all carry open bugs for
  broken Persian/Arabic/Hebrew rendering, and no vendor in the docs-AI category handles
  RTL properly. For a Persian product judged by Persian speakers, this is 55 points
  nobody is contesting.

Our constraint — that we hold no user credentials and cannot touch a Liara account — is
what makes the artifact-first approach necessary, and it turns out to be the lane the
credential-holding incumbents left empty.

## 3. Surfaces

Four entry points, one engine.

### 3.1 Ask — cited bilingual chat

The substrate. Hybrid retrieval over the docs, answers in the user's language, citations
deep-linked to the exact section. Everything in §5, §6 and §7 serves this.

### 3.2 Diagnose — paste the thing that broke

Accepts a build log, runtime crash, or `liara logs` output. A deterministic classifier
identifies the artifact by shape before a token is spent. Normalization strips ANSI codes
and timestamps, **redacts secret-shaped strings in-process so they never reach the LLM**,
and extracts a ±15-line window around the first line matching an anchor pattern — a
window, not the whole log, following Netlify's approach.

Matching has **no LLM in the decision path**. Signature cards carry anchor regexes,
required and negative tokens, and the platforms and deploy paths they are valid for. The
model writes prose around fixed slots; it never authors the fix.

### 3.3 Check — validate what you already have

Paste an existing `liara.json`, Dockerfile or nginx conf and get a per-file checklist
with findings, fix diffs, and the doc page behind each rule. **Two independent design
passes converged on this as the strongest entry point**, for the same reason from
opposite directions: every user has a config, but only a failing user has a log; and
catching a real bug in something the judge brought is more convincing than generating
something they cannot verify.

### 3.4 Generate — artifacts for a described stack

~4 gradient questions (workload shape, statefulness, traffic, budget) rendered as chips,
pre-filled from the saved profile. Produces `liara.json`, Dockerfile, `liara_nginx.conf`,
`liara_pre_start.sh`, `.liaraignore`, a GitHub Actions workflow, the env block for the
chosen database, and an ordered CLI runbook — all through the same validator as §3.3.

A router decides whether a message is artifact-shaped or prose-shaped. **Over-triggering
the wizard on ordinary questions trades 80 rubric points for 50** and is a real risk, so
the router defaults to chat.

## 4. The grounding asset — one extraction, four uses

A build-time pass over the corpus produces `manifest.json`: every real Liara noun —
`liara.json` field paths, platform enum values, CLI verbs and flags, env var names, plan
and region names, valid versions — each with the pages attesting it, its canonical URL,
and a support count. Built from **usage across the whole corpus**, not from the reference
pages, which is how it recovers `go.mainFile`, `django.settingsFile`, `image`,
`python.args` and `liara network create` — all real, all missing from the canonical
reference.

The same asset then serves:

1. **Anti-fabrication.** Symbols in high-precision syntactic positions (JSON keys inside
   fences, the token after `liara`, flags, env assignments) resolve against the manifest
   as the answer streams. Prose is never scanned — prose is where false positives live.
2. **Artifact validation.** The generator's output is checked against the same symbol
   table plus the rule tables in §8.
3. **Retrieval pre-filtering.** A question naming a service and platform hard-filters
   retrieval, so a Go+MongoDB question can never be served the Postgres-content page
   regardless of embedding similarity.
4. **Corpus defect detection.** See §9.

### Three verdicts, and why the middle one matters

- **known** → pass.
- **unknown but present verbatim in the retrieved context** → **pass**. The manifest is
  built by regex and will always have recall gaps; a gap must degrade to "unverified",
  never to "wrong". Killing a correct novel answer is the expensive failure.
- **unknown and absent from context** → violation. One repair pass with the offending
  symbols returned as a structured constraint. If the second draft still binds a phantom,
  the answer ships with the token marked `unverified` plus one honest sentence. We do not
  refuse — spurious refusal is a measured failure mode and users punish it harder than
  visible hedging.

### The coverage flaw, stated plainly

This layer is strongest on code-shaped claims, which is exactly where the model is
copying verbatim from retrieved fences and rarely inventing. It is **structurally blind
on UI procedures, causal claims, and plan/quota claims**, which bind no checkable symbol.
That blind spot is not incidental: 17% of pages carry their only instruction inside a
screenshot, and ~27 pages lost their code blocks in the markdown mirror, so on precisely
those questions invention is nearly forced.

A layer that passes those answers clean while stamping everything else "verified"
manufactures confidence in its weakest region. The remedy is to route **only the residue**
— sentences carrying no checkable symbol — to a ChainPoll verifier: boolean verdict,
reasoning before verdict, 5 samples, score = yes/total. Deterministic checking is free,
so the model call fires only where the free check cannot reach.

### Circularity, and the two-pass fix

The manifest is extracted from a corpus that is itself defective. `gorm.io/driver/postgres`
is genuinely attested on a MongoDB page. A naive build would bless the wrong answer with
the manifest's own authority. So: exact-duplicate detection runs **first** (it needs no
manifest), defect-flagged pages are excluded, and only then is the manifest extracted.

### The badge is silent until it earns visibility

The manifest will sometimes flag a correct symbol. A user who sees `unverified` on a
command that works stops reading the badge entirely — costing us the one occasion it was
right. The badge ships as an internal monitoring signal until it clears a measured
precision bar on the golden set.

## 5. Ingestion

**Crawl the rendered HTML**, not the MDX source and not the markdown mirror.

- The **MDX source** has zero fenced code blocks and zero `##` headings — code lives in
  `<Highlight>` template literals, structure in `<Section id title>`. A markdown-aware
  splitter finds nothing to split on and embeds React boilerplate. Stripping imports and
  JSX removes 40% of the bytes.
- The **markdown mirror** is clean but lossy — code-block dropout on ~27 pages including
  `paas/details/envs.md`, the most-linked page in the corpus.
- **Rendered HTML** has both: the browser resolved the JSX, `<Highlight>` became `<pre>`,
  and `<Section id>` is a real anchor. This is also what Liara's own indexer crawls.

The `#anchor` gives **deep links to the exact section**, which serves the "ارائه منبع
مناسب" sub-criterion directly. Every page's `Original link:` header supplies the canonical
human URL for free.

Rewrite all relative links to absolute at ingest. Drop `/ai/ai-sdk-ui/chatbot.mdx` — a
296 KB file whose base64 blob accounts for 11.2% of all chunk tokens.

**Chunking:** split on `<Section>`, falling back to H1 plus size packing. ~400 tokens
measured with **BGE-M3's tokenizer, not cl100k** — Persian costs 3.45 tokens/word under
cl100k versus English's 1.29, so a "400-token" chunk holds 2.7× less Persian text than
English intuition suggests. Zero to 15% overlap (measured: 400/0 beat 400/200 on both
recall and precision). Never split a code block. **Prepend the heading breadcrumb into
the embedded text** — metadata that isn't embedded doesn't help retrieval. Store
`parent_section_id` and return the whole section to the model. Yields ~4,700 chunks.

## 6. Retrieval

**Embeddings: BGE-M3.** Persian MIRACL nDCG@10 of 61.38 versus OpenAI
text-embedding-3-large's 41.67 — cross-validated three ways. $0.01/M via OpenRouter, so
**1.7 cents to embed the entire corpus**. Cost is irrelevant here; optimize purely for
quality. 1024 dims also stays under pgvector's 2,000-dim index ceiling, which a 3072-dim
model would breach.

**Hybrid, dense-dominant.** Persian BM25 is weak (0.333) while dense is strong (0.480),
fusing to 0.594 — hybrid buys more in Persian than in most languages. Start α ≈ 0.7 dense.

**The lexical leg splits by script**: BGE-M3's own learned sparse head for Persian prose
(45.1 versus BM25's 28.7 on Persian, at no extra inference cost since we run the model
anyway), and BM25 over `to_tsvector('simple', …)` for Latin/CLI tokens where exact match
is the entire point — `liara.json`, `collectStatic`, `client_max_body_size`.

**Never `to_tsvector('arabic', …)`.** Its stemmer strips what it thinks are definite
articles: `برای` → `رای`, and **`لیارا` → `لیار`**. It mangles the client's brand name.
Postgres ships no Persian configuration; we normalize ourselves.

**Fusion:** RRF to start, switching to convex combination with theoretical min-max
normalization once ~50 labeled queries exist — worth 2–6% and the queries are the golden
set we are building anyway. Do not tune `k`; its effect is ~1% against a ~6% gap.

**Rerank:** pull 100–200 per leg, cross-encode top 50–150, keep 20. Qwen3-Reranker-0.6B
(Apache-2.0) as default. **No Persian reranker benchmark exists** — this one is
extrapolation and must be measured, not trusted. Avoid Jina rerankers: CC-BY-NC-4.0,
not commercially usable.

**Store:** pgvector, HNSW m=16 / ef_construction=64 (1.2 ms at 99.9% recall, 4.8 s build),
and `ALTER COLUMN embedding SET STORAGE PLAIN` — which halves exact-scan latency *and*
shrinks total storage.

### Persian normalization

Order is load-bearing: **NFKC → fold → ZWNJ policy → collapse whitespace.**

NFKC alone is not enough — it fixes presentation forms and ligatures but does nothing for
Arabic-versus-Persian variants, digits, or ZWNJ. Fold yeh, kaf, heh, alef and waw
variants; Persian and Arabic-Indic digits to ASCII; delete tashkeel and tatweel; bidi
marks to space.

**Never NFD-then-strip-combining-marks**: `ۀ` decomposes to U+06D5, which is a *letter*,
survives mark-stripping, and is not `ه`.

Measured cost of skipping this: a user on an Arabic keyboard loses **40%** of correct
results; tashkeel costs 60%.

**ZWNJ has no dominant policy** — 32.4% of distinct Persian word types in this corpus
contain one, and nine words appear both ways *within the corpus itself*. Splitting
recovers the spaced spelling and loses the joined one; joining does the reverse. **Emit
both variants at query time.**

**Reuse Liara's keyboard-layout synonym table.** Their indexer maps product names to
Persian-layout mojibake — `react → قثشزف`, `django → یتشدلخ`, `mysql → پغسضم` — which is
what you get typing the English word with the Persian layout active. Iranian developers do
this constantly, and no normalizer or embedding model will ever match these strings.

## 7. Evaluation

**Retrieval metrics do not predict answer quality.** Four independent confirmations,
including one measuring contextual precision at −0.02 correlation with expert judgment
while answer-correctness hit 0.88. Ericsson's failure attribution on a technical-docs RAG
found **generation-side failures outnumbered retrieval-side 3:1**. Use retrieval metrics
to localize a problem, never to gate a release.

**Golden set:** ~150 queries. Sourced preferentially from real questions, with 15–20%
deliberately unanswerable. Score with a fact-list rubric (all key facts = 1.0 / core fact
present = 0.5 / incorrect = 0.0), not answer similarity. **Record the corpus snapshot
version with every score.**

**Write the ~80-line harness ourselves.** Ragas is effectively unmaintained since
February, and its deterministic metrics compare spans by Levenshtein, which breaks in
exactly the short-gold/long-chunk case that is normal here. Use its `TestsetGenerator` to
bootstrap multi-chunk gold, then discard the library.

Track **recall@20 and distractor count together**. Topically-related-but-answer-free
documents degrade accuracy by up to 67% while *random* documents can improve it, so
precision@k is the wrong target and a change raising both recall and distractors can make
answers worse.

**LLM-as-judge is unreliable in Persian.** Stylistic preference judging agrees with humans
~85%, but *objective correctness* judging — which is what faithfulness is — sits near
random for vanilla frontier models, multilingual judge consistency is κ≈0.3, and no study
breaks Persian out. Mitigations: reference-guided judging, position swapping, a different
model family than the generator. **Hand-label 25–30 Persian pairs, compute judge–human
agreement, and publish that number beside every judged metric.** Below ~70%, report
retrieval metrics only.

**Never let the reranker and the relevance judge share a model family** — under
circularity, system-ranking correlation degrades from τ=0.63 to τ=−0.40.

### Self-evaluation gates

We do not rely on a human to discover breakage. Per `../AGENTS.md`: `make check` for
static gates, `make up` + `make e2e` for integration, a browser-driven visual pass with
screenshot review for the UI quality that no assertion covers, the golden set for
retrieval, and `EVALUATION.md` giving every rubric sub-criterion a verdict and evidence.

## 8. Validation

The LLM emits a **typed `DeploymentSpec`** — platform, version, plan, deploy path,
database, needs_disk/cron/healthcheck/nginx. A deterministic renderer expands that spec
through templates into files. **The model never writes config text**: a model that cannot
type a key into a file cannot hallucinate one.

Four layers, roughly 85–90% deterministic because the field space is genuinely closed:

1. **JSON Schema** over `liara.json` with `additionalProperties: false`, per-platform
   `if`/`then` branches, and version enums harvested from the docs.
2. **Rule table** (YAML: id, severity, applies_to, predicate, bilingual message, doc_url,
   autofix). Includes the traps Liara's own docs contain — `healthCheck` intervals under
   1000 ("this is N milliseconds", with an ×1000 autofix); an `envs` block at all (a
   blocking notice, since it destructively replaces every existing variable); `app` or
   `platform` present on the GitHub deploy path (error, autofix delete); `laravel` with no
   explicit `phpVersion` (error by policy — `laravel` defaults to 7.4 while `php` defaults
   to 8.0, so a user who said "PHP 8" silently gets 7.4).
3. **Plan gate** — a pure table lookup. Zero-downtime on Bronze, backups on Bronze,
   disk counts over tier max, estimated build time over the 5/10/20-minute cap, and
   procedures the tier cannot perform at all (the documented disk shrink needs a second
   disk plus a backup, so Bronze literally cannot execute it — stated before step one
   rather than discovered at step four).
4. **Cross-artifact invariants** — the class no single-file validator catches. Port
   agreement across `liara.json`, Dockerfile `EXPOSE`, nginx `proxy_pass` and the app
   bind. `.liaraignore` not excluding a path the Dockerfile `COPY`s, and everything
   `.gitignore`/`.dockerignore` were relied on for re-listed, since `.liaraignore` fully
   suppresses both. Migrations appearing only in `liara_pre_start.sh`, the sole hook with
   env vars. The workflow's trigger branches matching the branch its shell condition tests
   — the exact bug in Liara's own documented example.

Real parsers, no new services: `jsonschema`, `crossplane` for nginx, `bash -n` plus
shellcheck, `actionlint`, `croniter`, `zoneinfo`. All milliseconds, which is what lets the
checklist be honest rather than decorative.

### Honesty mechanics

The load-bearing risk is **a green checklist on a config that would not actually deploy**.
Generator and validator are built from the same harvest, so a misreading is correlated:
the generator emits the wrong thing and the validator blesses it — strictly worse than a
chatbot that merely guessed, because we removed the user's suspicion.

The mitigation is scoping the claim, not widening coverage:

- Every check names exactly what it compared and cites the doc URL it compared against.
- Checks that did not run render as **"not checked"**, never folded into the pass count.
- The summary says "12 checks ran, 3 areas unverified" — never "validated".
- The rule table is versioned and findings record the rule version, so a contradiction
  found later is a data change with a test, not a prompt tweak.

## 9. Defective documentation

Liara's docs contain verified errors that perfect retrieval will serve confidently: a
MongoDB+Go page byte-identical to the PostgreSQL one, a Redis/.NET page titled "Redis in
Flask apps", `rabbitmq/create-user` containing MariaDB content, `paas/update.md` with its
Console and CLI headings swapped, and a CI/CD example that triggers on `main` while
testing `refs/heads/master`.

**Behaviour: answer from elsewhere, then name the defect below the answer, with evidence,
keeping the bad page in the citation list marked bad.**

Below the answer because the user asked a question and deserves the answer first. With
specific evidence because an accusation this strong must be checkable. Silent exclusion is
the choice most teams will make and it is wrong — the broken page stays live and
top-ranked, so a user we quietly routed around finds it an hour later, ships GORM into a
MongoDB service, and correctly blames us for having known and said nothing.

**Only near-zero-false-positive defect classes earn a user-visible accusation**:
byte-identical pages across different services, title/content mismatch confirmed by an
import statement, "run the command below" with no fence after it. Soft signals such as
0.5 Jaccard similarity get no accusation at all — they only downweight retrieval and feed
the internal dashboard. Publicly calling a correct page broken would be a trust
catastrophe, and that asymmetry is what sets the bar.

This is the only point in the product where the assistant can be **demonstrably more
correct than its own source of truth**. Any RAG bot can quote the docs; only one that
knows where they are broken can beat them.

## 10. Interface

Persian-first with a full English toggle, and **RTL done properly** — an open goal, since
no vendor in the category handles it and the major coding agents all carry open bugs for it.

The non-negotiable rule: **prose follows the user's language; identifiers, CLI flags, env
var names, code blocks, file paths, diffs and terminal output stay canonically English and
LTR.** A Persian answer that RTL-mangles a shell command so copy-paste silently breaks is
a whole category of ticket that looks like a language feature working correctly.

Implementation: `dir="auto"` with `unicode-bidi: plaintext` so each paragraph takes
direction from its first strong character; RTL detection by Unicode range; `row-reverse`
for RTL message rows; code containers pinned LTR regardless of surrounding direction.

Proven patterns worth adopting rather than reinventing: claim-level inline citation
markers with a hover popover and a separate sources panel; anchor-level deep links (only
Redocly and ReadMe do this — most competitors are page-level); clarifying questions as
**selectable cards, not free text**; structured downvote reasons rather than a scalar;
`Cmd/Ctrl+K` for search and `Cmd/Ctrl+I` for the assistant, a convention three vendors
adopted independently; a streaming renderer that handles syntactically incomplete markdown
mid-stream; and on small viewports a sources *sheet*, not a narrowed column.

Component reuse order per `../AGENTS.md`: existing project primitives → shadcn registry
(which covers chat interfaces) → existing dependency → new code with a recorded reason.

## 11. Operations and cost

- **Rate limiting** per user and per IP with a hard daily ceiling. Reference points from
  the field: 120 req/min, or ~300/user/day plus 60/min/team framed as surge protection.
- **Model ladder.** A cheap model triages and answers simple questions; the expensive one
  is reserved for genuine complexity. Agentic loops cost ~4× chat and multi-agent ~15×.
- **Caching keyed to document chunks, not embeddings.** MinHash + LSH over word shingles,
  with entries **cleared when their source chunks change** — the correct staleness answer
  for documentation, and cheaper than semantic caching, whose failure mode is real ("Python
  tutorial" matching "Python snake care" at 0.76 similarity).
- **Listwise context pruning** if time allows: scoring all retrieved chunks together
  rather than pointwise drops ~68% of chunks at ~96% recall for −34% net cost. Note it
  costs ~0.7 s of latency — it pays in money, not speed.
- **Prompt caching** is a prefix match; any byte change invalidates everything after it.
  Keep volatile content after the last breakpoint. Verify with `cache_read_input_tokens`;
  a persistent zero means a silent invalidator such as a timestamp in the system prompt.
- **Full request tracing** — question, retrieved chunk ids, model, tokens, latency,
  feedback — into Postgres, surfaced as a "worst answers this week" operator view. One
  published deployment could compute *no* retrospective faithfulness metric because
  retrieval spans were never logged. Instrument before it is needed.
- **Degraded mode**: if the LLM provider is down or over budget, fall back to pure
  retrieval and return ranked passages labelled "search results, not an answer".
- **Secrets** via `SecretStr` settings, never in `VITE_*`. Secret-shaped strings in pasted
  artifacts are redacted in-process before anything leaves our backend.

## 12. What we are deliberately not building

Recorded so they are not silently reconsidered:

- **Anything requiring population-scale traffic or elapsed time** — cross-user failure
  propagation, decaying per-topic mastery scores, quorum-triggered docs reports,
  nocturnal batch consolidation. Elegant mechanisms that render as empty states in a
  hackathon demo.
- **A mock of Liara's dashboard.** Enormous to build, stale the moment Liara ships a UI
  change.
- **Fog-of-war documentation maps, speedrun timers, named boss-fight encounters.**
  Decoration. They look agentic without making anyone's deploy faster, and criterion 3
  rewards the latter.
- **A Persian voice lane.** Genuinely high fit — the briefing named phone calls as the
  cost centre — but realtime Persian voice would consume the schedule that the other five
  rubric categories need.
- **Semantic chunking.** Fixed-size chunking consistently beats it, and it is a build.
- **Acting on a user's Liara account.** Settled: we hold no user credentials.

## 13. Live risks

1. **A wrong diff is worse than no diff.** The same symptom has different correct fixes
   depending on deploy path — adding `platform`/`app` to `liara.json` is right on CLI and
   Console and *fails the deploy* on GitHub. The judges are Liara's own engineers. Hard
   gate: never emit a diff unless platform and deploy path are both known.
2. **We have the fix half of every error signature and not the symptom half.** The docs
   name `GUNICORN_TIMEOUT` but contain no sample log text. Anchors must come from the
   upstream tools' own canonical output, and from logs we generate ourselves by
   deliberately breaking a dozen deploys on our credited account. That capture is also the
   test fixture set and the demo script.
3. **Grounding coverage is anti-correlated with fabrication risk** (§4).
4. **The reranker choice is extrapolated**, since no Persian reranker benchmark exists.
5. **No retrieval quality claim here has been validated end-to-end on our data.** Every
   number is a published benchmark or a component measurement. The golden set comes before
   trusting any of it.
