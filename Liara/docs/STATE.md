# STATE

The current status of the Liara challenge work. **Read this first** when starting or
resuming — it is the only document that reliably survives a context compaction or a
handoff to a different agent.

Keep it true as work happens, not tidy at the end. Nothing is marked done before it has
passed the verification gate in `../AGENTS.md`.

**Last updated:** 2026-08-20

---

## Where we are

Scaffolding and design are done. No application code has been written yet. The next
working session is the first build step: the grounding manifest and the validator, both
of which are testable offline with no LLM, no frontend, and no Liara account.

## Settled

Decisions that are made. Do not silently relitigate these; change them deliberately and
record why.

| Decision | Choice |
|---|---|
| Repository layout | All three challenges live in one monorepo, each self-contained |
| Base | The shared root `template/`, deviating only where a deviation genuinely improves things |
| LLM hosting | A third-party provider. Only the application itself is deployed to Liara |
| Agent scope | Guides the user and generates artifacts for them to run. It does not act on a user's Liara account, so no user credentials are held |
| Language | Fully bilingual Persian/English with an explicit toggle |
| Personalization | User accounts with a saved profile persisting across conversations |
| Ports | Vite 5174, API 8002, Postgres 5434 |
| Product shape | Four surfaces over one engine: Ask (cited chat), Diagnose (paste a log), Check (validate an existing config), Generate (artifacts from a described stack). See [`DESIGN.md`](DESIGN.md) |
| Embeddings | BGE-M3 via OpenRouter — [`decisions/0001`](decisions/0001-embedding-model.md) |
| Ingestion | Crawl rendered HTML — [`decisions/0002`](decisions/0002-ingestion-source.md) |
| Config generation | LLM emits a typed spec; deterministic code writes every file — [`decisions/0003`](decisions/0003-llm-never-writes-config.md) |
| Defective docs | Named below the answer with evidence — [`decisions/0004`](decisions/0004-defective-page-disclosure.md) |
| Not building | Anything needing population-scale traffic, a mock Liara dashboard, voice, gamification. Full list in `DESIGN.md` §12 |

## Done

- [x] `CHALLENGE.md` — requirements and the 300-point rubric recorded from the briefing
      video and challenge page
- [x] Template copied into `Liara/` with per-app identifiers applied — compose project
      names, image tag, uvicorn port, Vite port and proxy target, Playwright base URL
- [x] `AGENTS.md` written, with `CLAUDE.md` symlinked to it
- [x] `shadcn` skill installed project-locally at `.agents/skills/shadcn`
- [x] Research: Liara's services, deploy journey and documentation defects; the docs-AI
      competitive landscape; Persian/bilingual retrieval with measured benchmarks
- [x] Divergent ideation across five isolated frames, scored and converged
- [x] `docs/DESIGN.md` and the first four decision records

## In progress

Nothing.

## Next

Ordered by **where the points are**, not by what is most interesting to build. Answer
quality plus UI/UX is 135 of 300 against 50 for the agentic lanes, so retrieval quality is
the riskiest thing in the project — excellent agentic surfaces on mediocre retrieval score
worse than excellent Q&A alone. Step 2 precedes it only because it is a single offline
afternoon that the retrieval work then reuses — the manifest is also the retrieval
pre-filter, so building it first is not a detour.

1. **Smoke-test the inherited stack** — `make install`, `make dev`, `make up`. Confirm the
   template runs clean on the new ports before building on it.
2. **The manifest, one symbol class.** Parse every fenced ```json block in the corpus,
   flatten to dotted key paths, emit `data/manifest.json`, and diff it against the
   canonical `liara.json` reference page. One afternoon, no LLM, no frontend. It yields
   the highest-fabrication-risk symbol class, the shared harness every later extractor
   reuses, and a self-proving finding: the reference page omits `go.mainFile`,
   `django.settingsFile`, `image`, `python.args`, and leaves `go` out of the platform enum.
3. **Ingestion and retrieval**, per `DESIGN.md` §5–6 — the crawl, Persian normalization,
   chunking, embeddings, hybrid retrieval. Snapshot and version the crawl output so scores
   stay comparable. **This is the 135-point path and it starts now, not after the agentic
   lanes.**
4. **The golden set, before trusting any retrieval number.** ~150 queries, 15–20%
   unanswerable, fact-list rubric, corpus version recorded with every score. Weight it
   toward the multi-hop questions in `DESIGN.md` §3.1 — those are what the rubric means by
   "complex", and a set of easy lookups will report a healthy number while the product
   fails the questions that matter.
5. **The Q&A surface end to end** — cited answers, deploy-path disambiguation, the
   Console-only surface, the refusal contract, conversation continuation. Bilingual and RTL
   from the first commit rather than retrofitted.
6. **Prove the visual review loop.** Driving the running app in a browser and reviewing
   screenshots is load-bearing for the 55 UI/UX points and for the promise that we
   self-evaluate rather than relying on a human to find breakage. Prove it as soon as there
   is a real page to look at.
7. **The validator and its fixtures.** `liara.schema.json`, `rules.yaml`, `plans.yaml` and
   a pure `validate(bundle) -> list[Finding]`, with ~15 fixture pairs whose broken half is
   copied verbatim from Liara's own documentation. Testable with no model, no frontend and
   no Liara account. If it cannot go green in a day, the idea is wrong cheaply.
8. **Break our own deploys.** Deliberately fail ~12 deploys on the credited Liara account,
   one per error cluster, and capture the verbatim logs. This is the only source of Liara's
   actual log framing, and the captures triple as matcher fixtures, regression tests and
   demo script. No competitor working from documentation alone can do this.
9. **`docs/EVALUATION.md`** — all 27 rubric sub-criteria mapped to concrete checks with a
   verdict and evidence each.

## Blocked

Nothing.

## Notes worth keeping

- Two independent design passes converged on the same entry point from opposite
  directions: validate the config the user already has. Every user has a config; only a
  failing user has a log — and catching a real bug in something a judge brought is more
  convincing than generating something they cannot verify.
- The MCP-server / agent-skills lane was investigated and **rejected as a differentiator**:
  a dozen vendors ship it and it is now table stakes. Offer it so its absence does not look
  dated; expect no points for it.
- The docs give us the *fix* half of every error signature and almost never the *symptom*
  half — `worker-timeout.md` names `GUNICORN_TIMEOUT` with zero sample log text. Symptom
  anchors have to come from the upstream tools' own canonical output (`[CRITICAL] WORKER
  TIMEOUT`, `413 Request Entity Too Large`, `419 | PAGE EXPIRED`) and from logs we capture
  ourselves.

- Liara publishes an LLM-ready documentation mirror: `docs.liara.ir/llms.txt` indexes
  it, `all-links-llms.txt` lists every page, and `docs.liara.ir/llms/**/*.md` serves
  clean markdown — 1142 files, ~4.5 MB, no MDX to strip. Each file opens with an
  `Original link:` line giving its canonical URL, which is what citations should use.
- The docs repository's own indexer uses Meilisearch.
- The dev Compose stack installs dependencies inside the container with no package-cache
  mount. Named volumes are scoped per Compose project, so each challenge downloads its
  dependencies once. Worth a host cache mount if that download becomes painful.
