# Postgres as a platform

> The authoritative, in-depth reference is the
> [`postgres-as-platform`](../skills/postgres-as-platform/SKILL.md) skill and its
> `references/`. This page is the high-level summary + decision rationale.

## The principle

**One Postgres service, many capabilities.** If an extension provides a
capability, use it instead of introducing Redis / a vector DB / a broker / a
scheduler. The compose stack is therefore `postgres` + `agent` only.

## Tier model

### Tier 1 — core, installed in dev AND prod

| Extension | Capability | Workflow class | Install reality |
|---|---|---|---|
| **pgvector** | vector storage / similarity search (RAG) | all | hard guarantee (base image) |
| **pgai** | in-DB LLM / auto-embedding (Vectorizer) | all | best-effort (non-fatal if absent) |
| **pgmq** | in-DB task queue / fan-out | multi-platform publish | strong (PGDG apt) |
| **pg_cron** | scheduled dispatch | multi-platform publish | strong (PGDG apt) |

Install via `docker/postgres.Dockerfile`:
```dockerfile
FROM pgvector/pgvector:pg16
RUN apt-get update && apt-get install -y --no-install-recommends \
      postgresql-16-cron postgresql-16-pgmq && rm -rf /var/lib/apt/lists/*
```
(PGDG apt is preconfigured in the base image.) `extensions.sql` then runs the
`CREATE EXTENSION` statements idempotently; pgai is wrapped in a `DO $$ … EXCEPTION`
block so its absence only WARNs.

### Tier 2 — prod/compliance, opt-in (docs only by default)

PgBouncer (connection pooling), PostgreSQL Anonymizer (PII), PGAudit/pgMemento
(audit), wal-g/pgBackRest (backup). Enable via compose profile or prod build arg
when a concrete trigger fires — see
[`skills/postgres-as-platform/references/extension-tiers.md`](../skills/postgres-as-platform/references/extension-tiers.md).

### Tier 3 — situational, docs only

pg_search/ParadeDB (hybrid BM25 + vector), ZSON, hypopg, pg_partman.

## Decision matrix

| Need | Default | Escalate when… |
|---|---|---|
| Scheduled workflow trigger | `pg_cron` → `pgmq` | — |
| Short-term conversation memory | `PostgresSaver` | — |
| Cross-thread long-term memory | `PostgresStore` | — |
| Vector retrieval / RAG | `pgvector` (+ `PGVector`) | need BM25 hybrid → Tier 3 |
| In-DB LLM / embeddings | `pgai` | prefer external pipeline → demote to a Python `@tool` |
| Task queue / fan-out | `pgmq` | throughput > a few thousand msg/s → dedicated broker (rare here) |
| Connection management | direct | prod load → Tier 2 PgBouncer |
| Customer PII | plain columns | compliance → Tier 2 Anonymizer |
| Outbound HTTP (social platforms etc.) | Python `@tool` (httpx) | **never** push HTTP from the DB |

## Python surface — `platform.py`

Single module, lazy singletons, one `setup_all()`:

| Accessor | Returns |
|---|---|
| `get_saver()` | `PostgresSaver` (checkpointer) |
| `get_store()` | `PostgresStore` (long-term memory) |
| `get_pgmq()` | `PGMQueue` (from `tembo-pgmq-python`) |
| `get_vectorstore()` | LangChain `PGVector` |
| `schedule_job(...)` | pg_cron jobid (or None if unavailable) |
| `setup_all()` | idempotent startup (LangGraph tables + default queues) |

All agents/tools obtain Postgres handles **here**; nothing else reads `DB_DSN`.

## Networking rule (don't trip on this)

Inside a container, `127.0.0.1` is that container's loopback. Code running in
compose uses the **service name** `postgres` in `DB_DSN`; host-side tools
(`psql`, GUIs) use `127.0.0.1:5432` against the dev compose's published port.
See [`skills/postgres-as-platform/references/networking-rules.md`](../skills/postgres-as-platform/references/networking-rules.md).

## Verification note

`docker build` of the postgres image is **not run in this sandbox** (no Docker
Hub access). The Dockerfile uses the officially-documented PGDG apt install for
`postgresql-16-cron` / `postgresql-16-pgmq`; run
`docker compose -f docker-compose.dev.yml up` in a networked environment, then
`\dx` to confirm `vector`/`pg_cron`/`pgmq` are present (`pgai` is best-effort).
