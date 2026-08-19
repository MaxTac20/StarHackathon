# STATE

The current status of the Liara challenge work. **Read this first** when starting or
resuming — it is the only document that reliably survives a context compaction or a
handoff to a different agent.

Keep it true as work happens, not tidy at the end. Nothing is marked done before it has
passed the verification gate in `../AGENTS.md`.

**Last updated:** 2026-08-20

---

## Where we are

Scaffolding is in place. The product has not been designed yet, and no application code
has been written. The next working session is the design session.

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

## Done

- [x] `CHALLENGE.md` — requirements and the 300-point rubric recorded from the briefing
      video and challenge page
- [x] Template copied into `Liara/` with per-app identifiers applied — compose project
      names, image tag, uvicorn port, Vite port and proxy target, Playwright base URL
- [x] `AGENTS.md` written, with `CLAUDE.md` symlinked to it
- [x] `shadcn` skill installed project-locally at `.agents/skills/shadcn`

## In progress

Nothing.

## Next

1. **Design session** — decide what the product actually is, beyond "a chatbot over the
   docs", against the rubric. Produce `docs/DESIGN.md`.
2. **Ingestion approach** — Liara publishes an LLM-ready mirror of its docs. Decide how
   it is fetched, chunked, and refreshed, and record it in `DESIGN.md`.
3. **`docs/EVALUATION.md`** — map all 27 rubric sub-criteria to concrete checks. Some
   are assertable tests, some need a visual pass, and answer quality needs a golden set.
4. **Smoke-test the stack** — `make install`, `make dev`, `make up`, and confirm the
   inherited template runs clean on the new ports before building on it.
5. **Verify the visual review loop works** — driving the running app in a browser and
   reviewing screenshots is load-bearing for the 55 UI/UX points, so it needs proving
   early, not at the end.

## Blocked

Nothing.

## Notes worth keeping

- Liara publishes an LLM-ready documentation mirror: `docs.liara.ir/llms.txt` indexes
  it, `all-links-llms.txt` lists every page, and `docs.liara.ir/llms/**/*.md` serves
  clean markdown — 1142 files, ~4.5 MB, no MDX to strip. Each file opens with an
  `Original link:` line giving its canonical URL, which is what citations should use.
- The docs repository's own indexer uses Meilisearch.
- The dev Compose stack installs dependencies inside the container with no package-cache
  mount. Named volumes are scoped per Compose project, so each challenge downloads its
  dependencies once. Worth a host cache mount if that download becomes painful.
