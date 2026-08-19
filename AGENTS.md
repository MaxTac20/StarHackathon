# AGENTS.md

Workspace for a three-challenge hackathon. Each challenge is an independent
submission with its own deployed application.

## What lives where

| Path | Purpose |
|---|---|
| `ArvanCloud/` | Submission for the ArvanCloud challenge |
| `Liara/` | Submission for the Liara challenge |
| `ZarinPal/` | Submission for the ZarinPal challenge |
| `template/` | Shared starting point the challenge apps are copied from |
| `.agents/skills/` | Agent skills available to any tool, symlinked into `.claude/skills/` |

## Working inside a challenge directory

**Each challenge directory is owned independently and sets its own conventions.**
Before working in one, read its `AGENTS.md` if it has one, and follow that. If it has
none, use your own judgement within that directory.

Do not carry conventions, structure, or workflow from one challenge directory into
another, and do not add cross-challenge shared code. Keeping them independent is what
lets each be worked on separately — and lets any of them be split into its own
repository later with `git subtree split -P <dir>`, history intact.

This file describes what the directories are. It deliberately says nothing about how to
work inside any of them.

## The shared template

`template/` is a full-stack starter: FastAPI + PostgreSQL behind a React/Vite frontend,
built into a single production image, with Docker Compose stacks, Alembic migrations,
and lint/typecheck/test wiring behind a `Makefile`. Its own `AGENTS.md` and `README.md`
document its architecture and commands.

Copy it into a challenge directory rather than referencing it — each copy is
self-contained. Compose files use `context: ../..` relative to themselves, so a copy's
Docker build context is its own directory and never includes a sibling challenge.

### When copying it, change these

The template hardcodes identifiers that assume it is the only app on the machine. Two
copies left unchanged will fight over containers, volumes, images, and ports:

- `infra/compose/compose.yml` → `name:` (also scopes the Postgres volume)
- `infra/compose/compose.dev.yml` → `name:` and the host side of each port mapping
- `Makefile` and `compose.yml` → the `fullstack-starter:local` image tag
- `Makefile` → the `--port` passed to uvicorn
- `.env.example` → `PORT`
- `frontend/vite.config.ts` → `server.port` and the proxy target default
- `frontend/playwright.config.ts` → the `baseURL` default

Suggested port allocation so all three can run at once — a suggestion, not a rule:

| Challenge | Vite | API | Postgres |
|---|---:|---:|---:|
| ArvanCloud | 5173 | 8001 | 5433 |
| Liara | 5174 | 8002 | 5434 |
| ZarinPal | 5175 | 8003 | 5435 |

## Repository conventions

- Default branch is `main`.
- Keep changes scoped to one challenge directory per commit where practical.
- Never commit `.env`, credentials, or API keys. `.env.example` documents the contract.
