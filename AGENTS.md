# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview

- This is a FastAPI POS backend using async SQLAlchemy, Alembic migrations, JWT auth, MinIO storage, and a module-based structure.
- The app is Docker-oriented. `docker-compose.yml` runs the FastAPI service and MinIO; MySQL is configured through `.env` and may be a remote database connection rather than a local container.
- Keep changes aligned with the existing module pattern: `model.py`, `schema.py`, `service.py`, `route.py`, and `__init__.py` under `app/modules/<module_name>/`.

## Environment Rules

- Do not commit or print secrets from `.env`, `.env.prod`, database URLs, JWT secrets, SMTP credentials, MinIO keys, or payment gateway credentials.
- Treat MySQL as remote unless the user says otherwise. Avoid destructive database operations, resets, or broad migrations without explicit approval.
- Prefer Docker commands through `./docker.sh` when available:
  - Start services: `./docker.sh up`
  - Stop services: `./docker.sh down`
  - Create migration: `./docker.sh migrate:create "message"`
  - Apply migrations: `./docker.sh migrate:up`
  - View logs: `./docker.sh logs fastapi`
- If running locally outside Docker, use `uvicorn app.main:app --host 0.0.0.0 --port 8000` only after dependencies and `.env` are present.

## Module Structure Rules

- Add new business features as modules under `app/modules/<name>/`.
- Keep database models in `model.py`, Pydantic request/response models in `schema.py`, database/business logic in `service.py`, and FastAPI endpoints in `route.py`.
- Register new routers in `app/main.py` with the `/api/v1` prefix.
- Register new SQLAlchemy models in `migrations/env.py` so Alembic autogenerate can see them.
- Use existing response helpers from `app/core/response.py` (`success_response`, `error_response`) instead of returning ad hoc JSON.
- Use dependency injection from `app/core/database.py` and `app/core/dependencies.py` for DB sessions and authenticated users.

## Database And Migration Rules

- All schema changes must include an Alembic migration in `migrations/versions/`.
- Use UUID string primary keys (`String(36)`) to match existing models.
- Restaurant-scoped tables should include `restaurant_id` with `ForeignKey("restaurants.id", ondelete="CASCADE")` and an index.
- Prefer soft delete only when the existing module pattern uses it; otherwise use explicit delete behavior consistent with nearby modules.
- Keep migrations reversible with a valid `downgrade()`.
- Do not run `Base.metadata.create_all` as a replacement for migrations in production-like workflows.

## API Rules

- Keep routes REST-like and consistent with existing modules:
  - `POST ""` for create
  - `GET "/{id}"` for detail
  - `GET "/restaurant/{restaurant_id}"` for restaurant-scoped lists
  - `PUT "/{id}"` or `PATCH "/{id}/..."` for updates
  - `DELETE "/{id}"` for delete
- Protect admin or tenant data with existing auth dependencies unless the endpoint is intentionally public.
- Avoid returning raw secrets in API responses. For credentials, return masked values or `has_*` boolean flags.
- Keep request validation in Pydantic schemas using `Field`, enums, and optional types.

## Coding Style

- Follow the style already used in nearby modules; avoid unrelated refactors.
- Use async SQLAlchemy patterns: `select(...)`, `await db.execute(...)`, `await db.commit()`, and `await db.refresh(...)`.
- Keep service methods focused and reusable; keep routes thin.
- Use `extra_metadata` or `extra_config` instead of SQLAlchemy reserved attribute names like `metadata`.
- Store enum values as lowercase strings when matching API payloads and migration defaults.
- Keep code ASCII unless the file already uses non-ASCII text for a clear reason.

## Validation Rules

- For syntax checks, prefer `python3 -m compileall app migrations` or a focused path for changed modules.
- When dependencies are installed, validate imports with `python3 -c "from app.main import app; print(len(app.routes))"`.
- For database changes, run Alembic through Docker when possible: `./docker.sh migrate:up`.
- If validation cannot run because dependencies or services are missing, report exactly what was skipped and why.

## Safety Rules

- Every completed code or documentation change must be committed and pushed unless the user explicitly says not to.
- Before committing, review `git status --short` and avoid including unrelated user changes.
- Use concise commit messages that describe the module or behavior changed.
- Do not use destructive commands like `git reset --hard`, `git checkout --`, `docker compose down -v`, database drops, or migration downgrades unless the user explicitly requests them.
- Do not overwrite user changes in a dirty worktree. Inspect diffs before editing files that may have active user changes.
- Keep generated files, cache files, uploaded assets, logs, and local data out of commits unless specifically requested.
