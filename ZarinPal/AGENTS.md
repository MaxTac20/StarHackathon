# AGENTS.md

## Project overview

This is a deliberately simple full-stack starter:

```text
React/Vite -> FastAPI -> PostgreSQL
```

Development runs Vite and FastAPI separately for hot reload; Vite proxies relative `/api` calls. Production compiles React and copies it into one Node-free FastAPI application image. FastAPI serves API routes, assets, and the React Router SPA fallback. PostgreSQL remains a separate service.

## Repository map

- `backend/`: Python package, FastAPI app, Alembic migrations, pytest tests
- `frontend/`: React app, shadcn primitives, Vitest and Playwright tests
- `infra/docker/`: multi-stage application Dockerfile
- `infra/compose/`: production and development Compose files
- `docs/`: focused architecture, workflow, and deployment notes
- `Makefile`: canonical developer interface
- `.env.example`: documented configuration contract; never commit `.env`

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
