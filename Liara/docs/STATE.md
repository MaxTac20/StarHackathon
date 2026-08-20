# STATE

The current status of the Liara challenge work. **Read this first** when starting or
resuming — it is the only document that reliably survives a context compaction or a
handoff to a different agent.

Keep it true as work happens, not tidy at the end. Nothing is marked done before it has
passed the verification gate in `../AGENTS.md`.

**Last updated:** 2026-08-20

---

## Where we are

Scaffolding, design, and the first cited conversational surface are complete. Retrieval
and the remaining product lanes are still separate follow-up work.

**Working locally.** Liara credits have not been released, so checkpoint 0 — deploying a
hello-world to de-risk the 40 deployment points on day one — cannot run yet. This is the
exact risk `DESIGN.md` §12 ordered the sequence to avoid, so it is now deferred rather
than mitigated. Partial mitigation: build and run the production image locally with
`make up`, so when credits arrive the only unknown left is Liara's platform behaviour and
not our container. **Install `@liara/cli` and deploy the moment credits land**, regardless
of what else is in flight.

**Toolchain verified 2026-08-20:** uv 0.9.9 with CPython 3.14 already fetched, Node
24.11.1, pnpm 11.22.0, Docker 28.5.1 + Compose v2.40.3 running without sudo. `psql` is
absent locally, which is fine — Compose provides PostgreSQL. `liara` CLI not yet
installed.

**Secrets:** the OpenRouter key lives in the session scratchpad as `or.key`, never in the
repository. It was pasted into a chat transcript, so rotate it after the hackathon.

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
| Deadline | Submissions close the evening of **2026-08-21** |
| Driving model | `openai/gpt-5.6-luna` via OpenRouter, adaptive reasoning effort — `DESIGN.md` §13 |
| Everything else | Hosted APIs. The only thing we host is the application itself |
| Git workflow | Branch → PR → merge. No direct pushes to `main` |
| Remote | `origin` = MaxTac20/StarHackathon; `upstream` = pooya79/StarHackathon |
| Product shape | Four surfaces over one engine: Ask (cited chat), Diagnose (paste a log), Check (validate an existing config), Generate (artifacts from a described stack). See [`DESIGN.md`](DESIGN.md) |
| Embeddings | Qwen3-Embedding-8B via OpenRouter, requested at 1024 dimensions — [`decisions/0001`](decisions/0001-embedding-model.md) |
| Ingestion | One pinned sparse git clone: mirror text + MDX anchors + asciinema casts. No crawler — [`decisions/0002`](decisions/0002-ingestion-source.md) |
| Config generation | LLM emits a typed spec; deterministic code writes every file — [`decisions/0003`](decisions/0003-llm-never-writes-config.md) |
| Defective docs | Named below the answer with evidence — [`decisions/0004`](decisions/0004-defective-page-disclosure.md) |
| Not building | Anything needing population-scale traffic, a mock Liara dashboard, voice, gamification. Full list in `DESIGN.md` §14 |

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
- [x] Ingestion source re-decided against measurement of all 1,142 pages — `decisions/0002`
- [x] `docs/CONTRACTS.md` — the interfaces that let build streams run in parallel
- [x] Shared Persian normalizer (`app.utils.persian`) with behavioural tests
- [x] **Local toolchain verified end to end**: `make install` green, `make check` green
      (mypy 23 files, tsc, 3 tests, production build), `make up` green with a healthy
      container serving `/api/health` and the SPA on 8002
- [x] Corpus cloned, pinned and measured — see *Corpus snapshot*
- [x] Retrieval checkpoint 1: pgvector schema and HNSW/GIN indexes, Qwen3 embedding
      batches with retry-safe incremental persistence, fixture loading, ZWNJ-aware dense
      plus `simple` lexical search, and dense-dominant RRF. Verified against PostgreSQL 18
      and OpenRouter: the Persian fixture query `چطور متغیرهای محیطی را اضافه‌کنم؟`
      returned `paas/details/envs#add-envs:0` at rank 1 with the exact deep-link citation.
      Six fixture chunks used 460 tokens and 2.27 seconds of embedding API time, measuring
      $0.00077 per 1,000 fixture-sized chunks at $0.01/M tokens. The full corpus was not
      embedded. Two lexical defects found in review and fixed: query-side Persian function
      words are now filtered (`را` alone matched 5 of 6 chunks, and `simple` has no
      stopword list by design), and only the ZWNJ-stripped variant reaches the lexical leg
      — Postgres keeps ZWNJ inside the lexeme, so the preserved variant could never match
      the stripped index. Both were measured against a live database, not inferred. The
      index stays lossless; a 12-decoy PostgreSQL flooding regression and an adversarial
      top-three RRF test cover both.
- [x] `codex/liara-chat` conversational surface — database-free AI SDK v5 stub stream,
      replaceable answerer seam, Persian-first bilingual UI, citations, reasoning and
      source disclosure, resilient streaming markdown, code copy, and mixed-direction
      isolation. `make check` passes with 21 backend tests (1 skipped) and 30 frontend
      tests. Browser gates
      passed on local-only API `8012` and Vite `5184`: first status motion stayed below
      500 ms, all phases advanced, sources preceded answer text, incomplete links and
      fences remained visually valid, and 390x844 plus 1440x900 kept the composer visible
      without page-width overflow.
- [x] Chat bundle follow-up — replaced `@streamdown/code`'s all-language Shiki registry
      with ten explicit Liara-documentation languages and alias handling; unsupported and
      invalid-JSON fences stay plain text. The production artifact fell from 12 MB / 308
      JS chunks to 2.5 MB / 17 JS chunks. The initial HTML graph remains essentially flat
      at 404.19 KiB gzip (`-9`) because the highlighter was already lazy; it is dominated
      by the application/runtime entry and Streamdown's markdown/HTML parsing stack, not
      language grammars. The 390x844 browser pass confirmed visible syntax colors, a
      visible composer, and no page-width overflow in either direction.

## In progress

Three build streams run in parallel as Codex handoffs, each in its own git worktree on its
own branch, all cut from `main` at `b130cf2`. They share `docs/CONTRACTS.md` and nothing
else, and none of them may touch another's directory.

| Branch | Worktree | Scope |
|---|---|---|
| `codex/liara-ingest` | `../StarHackathon-codex-liara-ingest` | Corpus → `corpus.jsonl`, plus the manifest-key inventory |
| `codex/liara-retrieval` | `../StarHackathon-codex-liara-retrieval` | pgvector storage, embeddings, hybrid search. Its own Postgres on **5444** |
| `codex/liara-chat` | `../StarHackathon-codex-liara-chat` | `POST /api/chat` streaming + the chat UI, against a stub answerer. API **8012**, Vite **5184** |

Ports are deliberately off the defaults so the streams cannot collide with each other or
with `make up` in the main checkout. Each worktree has its own `.env` carrying
`OPENROUTER_API_KEY` and `INGEST_CORPUS_DIR`; those files are gitignored and must stay so.

Session ids are recoverable with `grep -m1 "session id:" <scratchpad>/codex-liara-<slug>.log`.

No work remains on the `codex/liara-chat` lane; it is committed on its branch and ready
for review. It deliberately remains unmerged.
- [x] Pinned-corpus ingestion: mirror Markdown joined with MDX anchors and OSC-2 cast
      commands, emitted as 5,250 validated records in `data/corpus.jsonl`; 1,973 chunks
      have deep-link anchors and 34 carry cast-sourced commands. The same pass emits 68
      observed manifest leaf paths in `data/manifest.json`. Fixture tests and
      `make check` passed on 2026-08-20.
- [x] Pinned-corpus ingestion: mirror Markdown joined with MDX anchors and terminal-replayed
      casts, emitted as 5,287 validated records in `data/corpus.jsonl`; 1,977 chunks have
      deep-link anchors and 103 carry cast-sourced commands. Replay recovers 108 command/result
      blocks from 89 of 90 cast files (`create-drizzle-app` has no command on its final screen).
      Credential-shaped content is redacted before storage: 246 redactions across 160 pages,
      including JWT, password-position UUID and generated-alphanumeric, and secret-labelled hex
      coverage added after an independent audit. The same pass emits 68 observed manifest leaf
      paths in `data/manifest.json`. All 5,287 records validate, a second pass over stored text
      and code finds zero residual redactions, required placeholders and unrelated UUIDs remain,
      the two output files reproduce byte-for-byte, and `make check` passed on 2026-08-20.

## In progress

Nothing.

## Corpus snapshot

`liara-cloud/docs` at commit **`31f2ef7`** (2026-08-15), fetched as a blobless sparse
clone over `src/pages public/llms public/casts indexer` — 24 MB, seconds. The default
branch is **`master`**, not `main`. Contents: 1,142 MDX pages, 1,142 mirror pages, 90
asciinema casts, and Liara's own Meilisearch indexer under `indexer/`.

A full `git clone` of this repo exceeds two minutes on this connection; always use the
sparse form.

## Open decisions, blocking checkpoint 1

1. **Personalization depth.** Session-scoped profile chips instead of user accounts?
   Drops auth, user storage, and a privacy surface that criterion 4 would then be judged
   on. The rubric's personalization language is *«شخصی‌سازی پاسخ‌ها»*, *«حفظ Context
   مکالمه»* and *«تجربه مناسب در ادامه Conversation»* — the scored object is the answer
   changing shape, never identity persisting across sessions or devices. The load-bearing
   cost is not the login form but SSE: `EventSource` cannot set an `Authorization`
   header, so auth means cookie semantics that differ between `localhost:5174` and the
   deployed origin — and that failure would surface on the environment we cannot reach
   until credits land. **Recommended: yes, session-scoped**, with a shareable session
   link (≈1 hour) as the demo beat instead. The profile is a typed object either way, so
   accounts stay an additive upgrade at checkpoint 5.

## Next

Ordered by **where the points are**, not by what is most interesting to build. Answer
quality plus UI/UX is 135 of 300 against 50 for the agentic lanes, so retrieval quality is
the riskiest thing in the project — excellent agentic surfaces on mediocre retrieval score
worse than excellent Q&A alone.

1. **Smoke-test the inherited stack** — `make install`, `make dev`, `make up`. Confirm the
   template runs clean on the new ports before building on it.
2. **Embeddings and hybrid retrieval**, per `DESIGN.md` §6, over the pinned
   `data/corpus.jsonl`: 1024-dimensional Qwen3 embeddings, normalized lexical search,
   fusion and reranking. **This is the 135-point path and it starts now, not after the
   agentic lanes.**
3. **The golden set, before trusting any retrieval number.** ~150 queries, 15–20%
   unanswerable, fact-list rubric, corpus version recorded with every score. Weight it
   toward the multi-hop questions in `DESIGN.md` §3.1 — those are what the rubric means by
   "complex", and a set of easy lookups will report a healthy number while the product
   fails the questions that matter.
4. **The Q&A surface end to end** — cited answers, deploy-path disambiguation, the
   Console-only surface, the refusal contract, conversation continuation. Bilingual and RTL
   from the first commit rather than retrofitted.
5. **Prove the visual review loop.** Driving the running app in a browser and reviewing
   screenshots is load-bearing for the 55 UI/UX points and for the promise that we
   self-evaluate rather than relying on a human to find breakage. Prove it as soon as there
   is a real page to look at.
6. **The validator and its fixtures.** `liara.schema.json`, `rules.yaml`, `plans.yaml` and
   a pure `validate(bundle) -> list[Finding]`, with ~15 fixture pairs whose broken half is
   copied verbatim from Liara's own documentation. Testable with no model, no frontend and
   no Liara account. If it cannot go green in a day, the idea is wrong cheaply.
7. **Break our own deploys.** Deliberately fail ~12 deploys on the credited Liara account,
   one per error cluster, and capture the verbatim logs. This is the only source of Liara's
   actual log framing, and the captures triple as matcher fixtures, regression tests and
   demo script. No competitor working from documentation alone can do this.
8. **`docs/EVALUATION.md`** — all 27 rubric sub-criteria mapped to concrete checks with a
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
- **This connection runs at 25–50 KiB/s to npm.** pnpm's default `fetch-timeout` is 60 s,
  so any tarball over roughly 3 MB (`lucide-react` is 2.75 MB) cannot finish and is
  discarded, then re-downloaded. `make install` fails on this, twice, with
  `TimeoutError: The operation was aborted due to timeout`. The fix is pnpm's own config,
  not environment variables — `npm_config_*` is ignored by pnpm 11:

      pnpm config set fetch-timeout 1800000 --location=user
      pnpm config set network-concurrency 2 --location=user
      pnpm config set fetch-retries 8 --location=user

  Lowering concurrency matters as much as the timeout: 16 parallel fetches split a slow
  link 16 ways and make every one of them time out. Never retry a failed install blindly —
  the pnpm store is content-addressed and keeps what already landed, so a retry after
  fixing the config resumes rather than restarts.
- **`liara.json` manifest, what is known so far.** 49 distinct key paths appear across the
  corpus's own examples (`app`, `port`, `image`, `disks.*`, `platform`, plus per-platform
  blocks for `node`, `django`, `go`, `laravel`, `next`, `angular`, `python`). The real
  reference page is `paas/liarajson.md` at 749 lines; `references/cli/create-liara-json.md`
  is 24 lines and documents no keys at all. A rigorous documented-versus-observed diff was
  **not** completed — the quick parser used was inadequate against that page's format, and
  building the inventory properly is part of the ingestion handoff. Do not quote a
  "documented keys" number until that lands.
- `make check` runs `build` last, so a stale `frontend/dist` from a previous run used to
  fail lint on every run after the first. Fixed by excluding build artifacts in
  `biome.json`. **The same latent bug is still in `template/`** and therefore in any copy
  made from it, including ZarinPal — worth mentioning to whoever owns those, but not ours
  to change.
- The production container answers `/api/health` but `openapi.json` reports zero paths in
  the production image. Harmless for serving; only matters if `make api-client` is ever run
  against the production stack rather than dev. Not investigated.
- **Lexical retrieval measured against the full 5,250-chunk corpus**, not the fixture.
  Persian is strong: all three probe questions returned exactly the right pages
  (`set-envs`, `worker-timeout`, `disks/*`). Two weaknesses are real and remain open:
  - The leg ORs every surviving term, so high-document-frequency *content* words
    dominate. `liara` appears on nearly every page, so `liara env:set` returns
    object-storage pages, and `413 Request Entity Too Large` misses the nginx upload page
    because `Request` matches everywhere.
  - `disks.mountTo` returns **zero** hits — a documented manifest key, tokenized as one
    lexeme that never matches the JSON fence spelling.

  The likely fix is AND-or-phrase semantics first with an OR fallback when the result set
  is too small, which is a retrieval-quality decision that should be **measured against a
  golden set rather than guessed at**. Folded into the answer-engine work, which owns
  answer quality end to end. Note this affects the lexical leg only; the dense leg carries
  natural-language questions, so the practical cost is lost help rather than active harm.
