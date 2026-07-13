# extension-bootstrap

## Table of Contents
1. [Where extensions get installed](#where-extensions-get-installed)
2. [extensions.sql](#extensionssql)
3. [Install-reality tiers](#install-reality-tiers)
4. [Startup ordering](#startup-ordering)

## Where extensions get installed

Two layers, in order:

1. **Image build** (`docker/postgres.Dockerfile`) — installs the extension *binaries* via `apt` (pg_cron, pgmq) so `CREATE EXTENSION` will succeed later. pgvector ships with the base `pgvector/pgvector:pg16` image.
2. **Container startup** (`docker/extensions.sql`) — runs `CREATE EXTENSION IF NOT EXISTS …` for each Tier-1 extension, idempotently.

Doing the binary install at image-build time (not in the app entrypoint) keeps the app entrypoint cheap and makes "is the extension present?" deterministic.

## extensions.sql

```sql
-- Tier 1 extensions, idempotent.

-- pgvector: hard guarantee (base image ships it)
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_cron: requires shared_preload_libraries='pg_cron' (set in postgresql.conf / compose)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- pgmq: requires the 'pgmq' schema; the extension creates it
CREATE EXTENSION IF NOT EXISTS pgmq;

-- pgai: best-effort. Heavier; may be absent on some images. Non-fatal.
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS pgai;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'pgai not available (degraded mode): %', SQLERRM;
END $$;
```

Run via `psql "$DB_DSN" -f /docker/extensions.sql` from `entrypoint.sh` after the DB is healthy.

## Install-reality tiers

Determines how a missing extension is treated:

- **Hard guarantee** — pgvector. If `CREATE EXTENSION vector` fails, the build/startup **must fail loudly**. RAG is foundational.
- **Strong install** — pg_cron, pgmq. Installed via `apt` in the Dockerfile; `CREATE EXTENSION` should succeed. If it fails, surface the error (these are Tier 1 by decision).
- **Best-effort** — pgai. Wrapped in `DO $$ … EXCEPTION …`, emits a WARNING; workflows that need DB-side embedding fall back to a Python `@tool` (see [pgai-in-db-llm.md](pgai-in-db-llm.md)).

## Startup ordering

`docker/entrypoint.sh` (the agent service) must run, in order:

1. **Wait for Postgres health** — `until pg_isready -h postgres -U "$DB_USER"; do sleep 1; done`.
2. **Apply extensions.sql** — `psql` against the service-name DSN.
3. **platform.setup_all()** — `PostgresSaver.setup()`, `PostgresStore.setup()`, `ensure_queue(...)`, etc.
4. **Start the runtime** — `langgraph dev` (dev) / `langgraph up` or the prod equivalent.

postgres healthcheck (in compose) should be `pg_isready` so `depends_on: condition: service_healthy` actually waits for readiness, not just process start.
