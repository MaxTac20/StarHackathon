# Development

## Local workflow

Copy `.env.example` to `.env`, run `make install`, and use `make dev`. This starts Vite and Uvicorn with reload. Start only the development PostgreSQL service when database work is needed, then run `make db-upgrade`.

Use `make dev-docker` when local Python/Node installations are undesirable. Source is bind-mounted while virtual environments, node modules, and PostgreSQL data use named volumes.

## Typical changes

For a backend capability, add its schema, service function, and thin route, register the router, then add API tests. For a frontend capability, keep feature-specific API calls, query hooks, schemas, and components under `features/<name>`; pages should compose them.

After changing an API contract, run `make api-client`. After changing a model, import it from `db/base.py`, create a migration with `make db-revision MESSAGE="..."`, review it, and apply it.

Run focused tests while iterating and `make check` before finishing. `make format` applies the repository formatters.

## Useful URLs

- Vite application: <http://localhost:5173>
- FastAPI API: <http://localhost:8000/api/health>
- OpenAPI UI: <http://localhost:8000/docs>
- Readiness (includes PostgreSQL): <http://localhost:8000/api/ready>
