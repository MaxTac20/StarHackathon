# AGENTS.md — Liara Challenge

An LLM-based application that reduces Liara's documentation-driven support load.
Deployed to Liara's own infrastructure.

## Start here, every session

Read these two before making any change. This applies to a fresh session and to
resuming after a context compaction — nothing from a previous conversation is assumed
to survive.

1. **`CHALLENGE.md`** — what the challenge asks and the 300-point judging rubric. It is
   the reference every decision gets checked against. It records requirements only;
   it never contains design.
2. **`docs/STATE.md`** — where the work currently stands: what is done, what is in
   progress, what is next, what is blocked. This is the resumption point.

Then read `docs/DESIGN.md` for what we are building and why, if the work touches it.

## Documents and what each is for

| File | Holds | Changes |
|---|---|---|
| `CHALLENGE.md` | Requirements and rubric, as stated by the organisers | Only if the organisers clarify something |
| `docs/DESIGN.md` | Product and technical design — what we build, and why | On a design decision |
| `docs/STATE.md` | Current status ledger and next actions | Every working session |
| `docs/EVALUATION.md` | Each rubric sub-criterion mapped to a concrete check | As checks are added or run |
| `docs/decisions/` | One file per decision that had real trade-offs | On a decision worth explaining later |
| `docs/architecture.md`, `development.md`, `deployment.md` | Inherited template notes | On architecture or workflow change |

Keep them in their lanes. Requirements in `CHALLENGE.md`, rationale in `DESIGN.md` and
`decisions/`, status in `STATE.md`. A reader must be able to trust that `CHALLENGE.md`
is what was asked and not what we decided.

## Updating STATE.md

`STATE.md` is the only file that reliably carries work across a compaction or a handoff
to a different agent, so it must be true at all times rather than tidy at the end.

- Update it when a task's status changes — not in a batch at the end of a session.
- Record blockers with enough detail to act on: what was tried, what happened.
- Record decisions that are settled, so they are not silently relitigated. If a decision
  had trade-offs worth explaining, put the reasoning in `docs/decisions/` and link it.
- Never mark something done that has not passed its verification gate below.

## Reuse before writing

Check in this order, and stop at the first that fits:

1. Something already in this project — `frontend/src/components/ui/`, existing services,
   hooks, and helpers.
2. The shadcn registry, via the `shadcn` skill in `.agents/skills/`. It covers chat
   interfaces specifically. Add components with the project's package runner (`pnpm dlx
   shadcn@latest`) so they land as source under `components/ui/`.
3. An existing dependency already in `package.json` or `pyproject.toml`.

Only then write something new — and if it is a component you would have expected to
find, note in `docs/decisions/` why the existing options did not fit.

Do not invent an abstraction to avoid a small duplication. A local version that reads
clearly beats a shared one that does not fit.

## Verification gates

Nothing is "done" until it is shown working. We do not rely on a human to discover that
something is broken.

| Gate | Command | Covers |
|---|---|---|
| Static | `make check` | lint, format, strict typecheck, unit tests, production build |
| Integration | `make up` then `make e2e` | real flows against the production-style stack |
| Visual | drive the running app in a browser, capture and review screenshots | UI quality and UX detail, which no assertion covers |
| Retrieval | the answer-quality eval set | whether the right source is found and cited |
| Rubric | `docs/EVALUATION.md` | every sub-criterion has a verdict and evidence |

Run against the local production-style stack (`make up`) before anything is deployed.
A component is finished when it has passed its gate locally, not when the code compiles.

## Ports

Vite `5174`, API `8002`, Postgres `5434` — offset from the template so all three
challenge apps can run simultaneously.

## Backend architecture

Within `backend/src/app/`:

- `api/routes/`: HTTP parsing, dependencies, status codes, and response schemas
- `schemas/`: Pydantic request/response contracts
- `models/`: SQLAlchemy persistence models
- `services/`: business logic and use-case orchestration
- `db/`: engine, request-scoped sessions, declarative base
- `core/`: settings, logging, and security helpers

Keep routes thin: routes call services; services contain business decisions. Schemas define API contracts; do not expose database models as contracts by default. Read settings through `core/config.py`. Use request-scoped dependency-injected sessions—never add a global `Session`. The engine/session factory may be process-global. API routes live under `/api`.

Dependency direction should generally be `routes -> services -> models/db`, with schemas used at boundaries. Avoid imports from routes into services or models. Add abstractions only after a concrete repeated need exists.

## Frontend architecture

Within `frontend/src/`:

- `app/`: application initialization, router, and providers
- `features/`: feature-specific API functions, query hooks, schemas, and UI
- `components/ui/`: shadcn-generated or shadcn-style primitives
- `components/common/`: reusable application components
- `api/`: generic fetch infrastructure and generated OpenAPI types
- `pages/`: route-level composition
- `layouts/`: route layouts
- `lib/`: framework-independent helpers

Keep feature-specific code under its feature. Put genuinely reusable UI in `components`; leave shadcn primitives in `components/ui`. Use TanStack Query for server state—do not hand-roll server-state caches with `useEffect`. Forms use React Hook Form, Zod, and the existing resolver. API calls go through the API layer and always use relative `/api/...` paths; never hardcode a backend origin. Do not edit `api/generated/schema.ts` manually.

## Commands

- `make install`: frozen/locked dependency install
- `make dev`: local Uvicorn and Vite hot reload
- `make dev-docker`: containerized hot reload stack
- `make build`: frontend and production image build
- `make up`, `make down`, `make logs`: production-style Compose lifecycle
- `make lint`, `make format`, `make format-check`, `make typecheck`
- `make test`, `make test-backend`, `make test-frontend`, `make e2e`
- `make check`: all commit-gate checks plus frontend build
- `make db-upgrade`, `make db-downgrade`, `make db-revision MESSAGE="..."`
- `make api-client`: regenerate TypeScript types from FastAPI OpenAPI

## Adding a backend endpoint

1. Define request/response Pydantic models in `schemas/`.
2. Put business/database logic in `services/`.
3. Add a thin route module under `api/routes/` and use injected dependencies from `api/deps.py`.
4. Register its router in `api/router.py`; `/api` is added centrally.
5. Add API and service tests. Run `make api-client` if the public contract changed.

Use consistent HTTP status codes and the existing JSON error shape. Do not call `metadata.create_all()`.

## Adding a frontend feature

1. Create `features/<name>/` only with the subfolders needed now.
2. Add typed API functions using the generic API client and generated types.
3. Wrap server state in focused TanStack Query hooks.
4. Build feature components; keep route composition in `pages/`.
5. Register the route in `app/router.tsx` and add representative tests.

## Database migrations

Import new model modules in `app/db/base.py` so Alembic sees their metadata. With PostgreSQL running:

```text
make db-revision MESSAGE="describe the change"
```

Review the generated migration, especially defaults, constraints, data changes, and downgrade safety. Apply with `make db-upgrade`; revert one revision with `make db-downgrade`. Production runs `alembic upgrade head` as a one-shot migration service before the app starts.

## Code quality and constraints

Run `make check` before considering work complete. Update tests when behavior changes and documentation when architecture or workflow changes.

- Do not introduce a new framework when an existing dependency solves the problem.
- Do not add repository, CQRS, DDD, event-bus, or other abstractions speculatively.
- Do not bypass existing API/client patterns or duplicate existing utilities.
- Do not mix business logic into React components or FastAPI handlers.
- Keep changes focused; do not reformat unrelated files.
- Keep secrets out of source, logs, and all `VITE_*` variables.
- Use Alembic for every schema change.
- Preserve the single application-container production model and same-origin `/api` design.
