# Development

## Local workflow

Copy `.env.example` to `.env`, run `make install`, and use `make dev`. This starts Vite and Uvicorn with reload. Start only the development PostgreSQL service when database work is needed, then run `make db-upgrade`.

Use `make dev-docker` when local Python/Node installations are undesirable. Source is bind-mounted while virtual environments, node modules, and PostgreSQL data use named volumes.

## Typical changes

For a backend capability, add its schema, service function, and thin route, register the router, then add API tests. For a frontend capability, keep feature-specific API calls, query hooks, schemas, and components under `features/<name>`; pages should compose them.

After changing an API contract, run `make api-client`. After changing a model, import it from `db/base.py`, create a migration with `make db-revision MESSAGE="..."`, review it, and apply it.

Run focused tests while iterating and `make check` before finishing. `make format` applies the repository formatters.

## Loading the challenge dataset

Set `SEED_DATA_PATH` in the root `.env` when the CSV is not at the default
`data/challenge_data.csv` path. Relative paths are resolved from the ZarinPal challenge
directory. The seed command also reads the database connection from the existing
`DATABASE_URL` or `POSTGRES_*` settings.

Run `make db-seed` to apply pending migrations and load the file. The command calculates
the file's SHA-256 checksum: it skips an identical completed import and refuses to mix a
different file with existing data.

Run `make db-reseed` to intentionally replace the imported dataset. This command prints
a warning and transactionally clears only dataset imports, merchants, categories,
terminals, payment sessions, and payment tries. If validation or loading fails, the
transaction rolls back and the previous dataset remains available. Invoking the
explicit `db-reseed` target is the confirmation; there is no additional prompt.

The loader validates the source header, types, status values, row identity, and stable
session fields. Errors contain a CSV row number and a non-sensitive reason, never the
raw row or payer-card key. The supplied 473 MiB snapshot can take several minutes to
copy, normalize, and index depending on local PostgreSQL and disk performance.

## Useful URLs

- Vite application: <http://localhost:5173>
- FastAPI API: <http://localhost:8000/api/health>
- OpenAPI UI: <http://localhost:8000/docs>
- Readiness (includes PostgreSQL): <http://localhost:8000/api/ready>
