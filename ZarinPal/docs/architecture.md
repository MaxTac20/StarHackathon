# Architecture

## Boundaries and request flow

The browser renders the React/Vite application. Route-level pages compose feature code and shared UI. Server state enters through the generic API client and TanStack Query:

```text
React page -> feature query -> relative /api request -> FastAPI route -> service -> SQLAlchemy -> PostgreSQL
```

FastAPI routes validate request/response schemas and translate HTTP concerns. Services own business decisions. SQLAlchemy models describe persistence and are not API contracts by default. Database sessions are request-scoped dependencies.

## Serving models

In development, Vite (`:5173`) and Uvicorn (`:8000`) are separate processes. Vite proxies `/api` to Uvicorn, retaining same-origin browser behavior.

In production, Vite output is copied into the Python image. FastAPI serves:

- `/api/*` as JSON API routes
- `/assets/*` as immutable Vite assets
- other GET paths through `index.html` for React Router

The SPA fallback explicitly rejects unknown `/api` paths, so API 404s stay JSON 404s. PostgreSQL is always a separate service and is not exposed by production Compose.

## API typing

FastAPI's OpenAPI document is the source of truth. `make api-client` feeds it to `openapi-typescript`. Generated structural types are isolated from handwritten fetch/query code.
