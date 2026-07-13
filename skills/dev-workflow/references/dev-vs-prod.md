# dev-vs-prod

## Table of Contents
1. [Two standalone files](#two-standalone-files)
2. [Dev compose](#dev-compose)
3. [Prod compose](#prod-compose)
4. [What's different, at a glance](#whats-different-at-a-glance)

## Two standalone files

Per decision, dev/prod are **two fully separate files**, not an override stack:

- `docker-compose.dev.yml`
- `docker-compose.prod.yml`

Each is self-contained and readable in isolation. Trade-off: some duplication; benefit: no mental model of which override applies when.

## Dev compose

Goals: fast feedback, live editing, host-side introspection.

- `postgres`: builds `docker/postgres.Dockerfile` (Tier 1 extensions); named volume `pgdata_dev`; healthcheck; **publishes `5432:5432`** so host `psql`/GUI works.
- `agent`: builds `.` target=`dev` (`uv sync --all-extras --dev`); `command: uv run langgraph dev --host 0.0.0.0 --port ${PORT:-8000} --no-browser`; **mounts the project at `/app`** (hot reload); `depends_on: { postgres: { condition: service_healthy } }`; `env_file: .env`; `${PORT:-8000}:8000`.

Run:
```bash
docker compose -f docker-compose.dev.yml up
```

## Prod compose

Goals: reproducible, no source mount, restart-safe, locked deps, minimal surface.

- `postgres`: same image; named volume `pgdata_prod`; healthcheck; **does NOT publish** 5432 (internal only); `restart: unless-stopped`; stronger prod credentials from prod env.
- `agent`: builds `.` target=`prod` (`uv sync --frozen --no-dev`); no source mount; `restart: unless-stopped`; `env_file: .env` (prod); `${PORT:-8000}:8000`.

Run:
```bash
docker compose -f docker-compose.prod.yml up -d
```

## What's different, at a glance

| Aspect | dev | prod |
|---|---|---|
| Deps | `--all-extras --dev` | `--frozen --no-dev` |
| Source mount | yes (`/app`) | no |
| `langgraph` cmd | `langgraph dev` (reload) | `langgraph up` / prod server |
| Postgres published port | `5432:5432` (host tools) | not published |
| Restart policy | default | `unless-stopped` |
| Volume | `pgdata_dev` | `pgdata_prod` |
| Detached | interactive (foreground) | `-d` |
| Tier 2 extensions | not installed | optional (profile, see extension-tiers) |
