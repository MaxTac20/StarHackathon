SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help install dev dev-backend dev-frontend dev-docker db-up build up down logs lint format format-check typecheck test check test-backend test-frontend e2e db-upgrade db-downgrade db-revision db-seed db-reseed api-client data data-download clean

COMPOSE_PROD := docker compose --env-file .env -f infra/compose/compose.yml
COMPOSE_DEV := docker compose --env-file .env -f infra/compose/compose.dev.yml

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install locked backend and frontend dependencies
	cd backend && uv sync --all-groups
	cd frontend && pnpm install --frozen-lockfile

dev: ## Run local backend and frontend with hot reload
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

dev-frontend:
	cd frontend && pnpm dev

dev-docker: ## Run hot-reload development in Docker
	$(COMPOSE_DEV) up --build

db-up: ## Start only the development PostgreSQL container
	$(COMPOSE_DEV) up postgres -d

build: ## Build the frontend and production application image
	cd frontend && pnpm build
	docker build -f infra/docker/Dockerfile --target runtime -t zarinpal-dashboard:local .

up: ## Start the production-style stack
	$(COMPOSE_PROD) up --build -d

down: ## Stop production and development stacks
	$(COMPOSE_PROD) down
	$(COMPOSE_DEV) down

logs: ## Follow production stack logs
	$(COMPOSE_PROD) logs -f

lint: ## Lint backend and frontend
	cd backend && uv run ruff check .
	cd frontend && pnpm lint

format: ## Format backend and frontend
	cd backend && uv run ruff format .
	cd frontend && pnpm format

format-check: ## Check formatting without changing files
	cd backend && uv run ruff format --check .
	cd frontend && pnpm format:check

typecheck: ## Type-check backend and frontend
	cd backend && uv run mypy
	cd frontend && pnpm typecheck

test: test-backend test-frontend ## Run unit/API tests

test-backend: ## Run backend tests
	cd backend && uv run pytest

test-frontend: ## Run frontend unit tests
	cd frontend && pnpm test

e2e: ## Run Playwright smoke tests against E2E_BASE_URL (default localhost:8000)
	cd frontend && pnpm e2e

check: lint format-check typecheck test ## Run all pre-commit checks and frontend build
	cd frontend && pnpm build

db-upgrade: ## Apply all database migrations
	cd backend && uv run alembic upgrade head

db-downgrade: ## Revert one database migration
	cd backend && uv run alembic downgrade -1

db-revision: ## Create a migration: make db-revision MESSAGE="add users"
	@test -n "$(MESSAGE)" || (echo 'MESSAGE is required' && exit 1)
	cd backend && uv run alembic revision --autogenerate -m "$(MESSAGE)"

db-seed: db-upgrade ## Idempotently seed the payment dataset from SEED_DATA_PATH
	cd backend && uv run python -m app.cli.seed_data

db-reseed: db-upgrade ## WARNING: replace all imported payment dataset rows
	@echo 'WARNING: replacing all imported merchants, terminals, categories, sessions, and tries.'
	cd backend && uv run python -m app.cli.seed_data --replace

api-client: ## Regenerate TypeScript API types from FastAPI OpenAPI
	@schema_file=$$(mktemp); \
	trap 'rm -f "$$schema_file"' EXIT; \
	cd backend && uv run python -c 'import json; from app.main import app; print(json.dumps(app.openapi()))' > "$$schema_file"; \
	cd ../frontend && ./node_modules/.bin/openapi-typescript "$$schema_file" -o src/api/generated/schema.ts

data: data-download ## Download and extract the ZarinPal challenge dataset

data-download: ## Download and extract the ZarinPal challenge dataset
	bash scripts/download_data.sh

clean: ## Remove generated local build and cache artifacts
	rm -rf backend/.venv backend/.mypy_cache backend/.pytest_cache backend/.ruff_cache
	rm -rf frontend/node_modules frontend/dist frontend/coverage frontend/playwright-report frontend/test-results
