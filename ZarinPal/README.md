# ZarinPal Analysis Dashboard

Challenge 3 submission: an analysis dashboard for the supplied ZarinPal dataset. It
combines a FastAPI API, React client, and PostgreSQL without adding layers that a new
product does not yet need.

The submission is designed around the challenge's highest-value outcome: actionable,
original merchant insights whose calculations and contributing payment attempts can be
inspected in the UI. See the [challenge success criteria](docs/challenge-criteria.md)
for judging priorities, required deliverables, and the feature review checklist.

## Stack

- Python 3.14, FastAPI, Pydantic Settings, SQLAlchemy 2, psycopg, and Alembic
- React 19, TypeScript, Vite, React Router, and TanStack Query
- Material UI, MUI X, self-hosted Vazirmatn/Inter fonts, and Tailwind CSS 4 for
  approved fallback primitives
- Ruff, mypy, Biome, pytest, Vitest, Testing Library, and Playwright
- PostgreSQL 18, Docker, Docker Compose, uv, and pnpm

Production is one application image: a Node build stage compiles React, then a Node-free Python runtime serves `/api/*`, Vite assets, and the SPA fallback. PostgreSQL remains a separate private service.

## Quick start

Prerequisites: Python 3.14, [uv](https://docs.astral.sh/uv/), Node.js 24 Active LTS, pnpm 11, PostgreSQL 18, and Docker with Compose for container workflows.

```bash
cp .env.example .env
make install
make dev
```

First download and extract the challenge dataset:

```bash
make data-download
```

Open <http://localhost:5175>. Vite proxies `/api` to FastAPI at port 8003. API docs are at <http://localhost:8003/docs> in development. The dataset is stored locally as `data/challenge_data.csv.gz` and `data/challenge_data.csv`; `data/` is intentionally ignored by Git. See [the dataset script guide](scripts/README.md) for rerunning or refreshing it.

The application health endpoint does not require a database. Start PostgreSQL before using database-backed features:

```bash
make db-up
make db-upgrade
```

## Docker development

```bash
cp .env.example .env
make dev-docker
```

Open <http://localhost:5175>. Frontend, backend, and PostgreSQL run separately with source bind mounts and hot reload. The development database is bound only to `127.0.0.1:5435`.

## Production-style run

Change `POSTGRES_PASSWORD` and `SECRET_KEY` in `.env`, then:

```bash
make up
```

Open <http://localhost:8003> and <http://localhost:8003/example>. Compose first runs the one-shot Alembic migration service, then starts the application. PostgreSQL has no host port in production Compose.

To stop or inspect it:

```bash
make logs
make down
```

## Configuration

All backend configuration comes from environment variables through `backend/src/app/core/config.py`. Root `.env` is consumed by Compose; local backend commands also discover it. Copy `.env.example` and never commit `.env`.

Variables prefixed with `VITE_` are public and embedded in frontend assets. Never store secrets in them. API requests use relative `/api/...` URLs, so no CORS setup is needed in the normal workflow.

## Database migrations

```bash
make db-revision MESSAGE="add projects"
make db-upgrade
make db-downgrade
```

Import each new SQLAlchemy model in `app/db/base.py` before autogenerating. Production uses migrations and never calls `metadata.create_all()`.

## Tests and code quality

```bash
make lint
make format
make format-check
make typecheck
make test
make check
```

`make check` runs linting, formatting checks, strict type checking, backend/frontend tests, and a frontend production build. With the production stack running, install Playwright's Chromium once (`cd frontend && pnpm exec playwright install chromium`) and run `make e2e`.

Regenerate API types after changing FastAPI contracts:

```bash
make api-client
```

Generated OpenAPI types live in `frontend/src/api/generated/`; handwritten request functions remain under features or `src/api`.

## Repository structure

```text
backend/              FastAPI application, migrations, and tests
frontend/             React application, UI primitives, and tests
infra/docker/         Multi-stage production/development Dockerfile
infra/compose/        Production and hot-reload development stacks
docs/                 Architecture, development, and deployment notes
AGENTS.md              Rules and workflows for coding agents
Makefile              Stable developer commands
```

Start with the [challenge success criteria](docs/challenge-criteria.md),
[product brief](docs/product-brief.md), [design system](DESIGN.md),
[metric contracts](docs/metrics.md), and [data dictionary](docs/data-dictionary.md).
See [architecture](docs/architecture.md), [development](docs/development.md), and
[deployment](docs/deployment.md) for implementation and operations details.
