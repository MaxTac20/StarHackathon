# syntax=docker/dockerfile:1.7

FROM node:24.19.0-alpine3.23 AS frontend-base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable && corepack prepare pnpm@11.22.0 --activate
WORKDIR /app/frontend

FROM frontend-base AS frontend-dev
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
EXPOSE 5173
CMD ["pnpm", "dev"]

FROM frontend-base AS frontend-build
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.14.7-slim AS backend-base
RUN pip install --no-cache-dir uv==0.12.5
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app/backend

FROM backend-base AS backend-dev
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --all-groups --no-install-project
COPY backend/ ./
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM backend-base AS backend-build
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14.7-slim AS runtime
ENV PATH=/app/backend/.venv/bin:$PATH \
    PYTHONPATH=/app/backend/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    STATIC_DIR=/app/backend/static
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --home-dir /nonexistent app
WORKDIR /app/backend
COPY --from=backend-build --chown=app:app /app/backend/.venv ./.venv
COPY --chown=app:app backend/alembic.ini ./alembic.ini
COPY --chown=app:app backend/migrations ./migrations
COPY --chown=app:app backend/src ./src
COPY --from=frontend-build --chown=app:app /app/frontend/dist ./static
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
