# Deployment

## Image architecture

`infra/docker/Dockerfile` has independent frontend, backend dependency, and runtime stages. pnpm installs the frozen frontend lockfile and builds Vite. uv installs only frozen production Python dependencies. The final Python slim image contains neither Node.js nor pnpm, runs as UID/GID 10001, and serves both application halves through Uvicorn.

Build with `make build` or deploy `infra/compose/compose.yml`. Use a unique `SECRET_KEY`,
`APP_PASSWORD`, and PostgreSQL password in the deployment environment. Terminate TLS at
the platform/load-balancer level and forward proxy headers only from trusted
infrastructure if changing the included server command.

## Demo credential warning

The product intentionally defaults to `APP_PASSWORD=CHANGE_ME` and always shows that
default on the login screen, including production deployments. Override it for any
internet-accessible instance. This shared-password gateway is for judging and demos; it
does not provide named users, roles, audit attribution, password recovery, or merchant
identity authentication.

Sessions are signed by `SECRET_KEY`, stored in `HttpOnly` cookies, and expire after eight
hours. Changing `APP_PASSWORD` does not revoke already-issued cookies immediately. Rotate
`SECRET_KEY` to invalidate all active sessions, understanding that every viewer will be
signed out.

## Migrations

Production Compose runs the same application image as a one-shot `migrate` service (`alembic upgrade head`). The application starts only after that service succeeds and PostgreSQL is healthy. On other platforms, run the image once with `alembic upgrade head` before rolling out the web process. Do not run schema creation during application startup.

## Runtime behavior

The image exposes port 8000. `/api/health` reports process health; `/api/ready` checks PostgreSQL. React Router deep links are served by the SPA fallback. Unknown `/api` routes never fall through to HTML. PostgreSQL uses a named volume and has no published host port in production Compose.
