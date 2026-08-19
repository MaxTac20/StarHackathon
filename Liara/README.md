# Liara Challenge

An LLM-based application that reduces the support load caused by Liara's documentation
being large and hard to search — built for the Liara hackathon challenge and deployed to
Liara's own infrastructure.

## Orientation

| Document | What it is |
|---|---|
| [`CHALLENGE.md`](CHALLENGE.md) | What the challenge asks, and the 300-point judging rubric |
| [`docs/STATE.md`](docs/STATE.md) | Where the work currently stands |
| [`AGENTS.md`](AGENTS.md) | Working agreement for humans and coding agents |
| [`docs/architecture.md`](docs/architecture.md) | How the application is put together |
| [`docs/development.md`](docs/development.md) | Local development workflow |
| [`docs/deployment.md`](docs/deployment.md) | Deployment notes |

## Stack

FastAPI and PostgreSQL behind a React/Vite frontend, built into a single production
image. Copied from the workspace's shared `template/`; see the root
[`AGENTS.md`](../AGENTS.md) for what that template provides.

## Quick start

```bash
cp .env.example .env
make install
make dev
```

Vite serves <http://localhost:5174> and proxies `/api` to FastAPI on `8002`. These ports
are offset from the template's defaults so all three challenge applications can run at
the same time.

Production-style run, which is what gets verified before any deploy:

```bash
make up      # http://localhost:8002
make e2e
make down
```

Run `make check` — lint, format, strict typecheck, tests, production build — before
considering any change complete.
