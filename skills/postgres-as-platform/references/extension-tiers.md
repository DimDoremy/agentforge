# extension-tiers

## Table of Contents
1. [Tier model recap](#tier-model-recap)
2. [Tier 2 — prod/compliance, opt-in](#tier-2--prodcompliance-opt-in)
3. [Tier 3 — situational, docs only](#tier-3--situational-docs-only)
4. [How to enable a Tier 2 extension](#how-to-enable-a-tier-2-extension)

## Tier model recap

- **Tier 1** — core, installed in dev AND prod (pgvector, pgai, pgmq, pg_cron). See the SKILL.md matrix.
- **Tier 2** — prod/compliance, opt-in. Enabled via compose profile or prod-only install. Not in the dev image.
- **Tier 3** — situational, documented but never installed by default.

The harness ships at Tier 1. Escalate deliberately, with a concrete trigger.

## Tier 2 — prod/compliance, opt-in

| Extension / Tool | Purpose | Trigger to enable | Install surface |
|---|---|---|---|
| **PgBouncer** | Connection pooling | Agent/runtime opens many concurrent PG connections; seeing connection exhaustion or wanting to cap `max_connections` | Sidecar container or image entry; point `DB_DSN` at PgBouncer port (6432), not 5432 |
| **PostgreSQL Anonymizer** | PII masking/redaction | Customer-research storing PII subject to GDPR/PIPL/etc. | `CREATE EXTENSION anon;` + declare masking policy on tables |
| **PGAudit** | Session/object audit logging | Compliance requires an audit trail of who-read/wrote-what | Package install (`postgresql-16-pgaudit`) + `shared_preload_libraries` |
| **pgMemento** | Row-level change history | Need full row history / undo beyond standard triggers | `CREATE EXTENSION pgmemento;` + trigger registration |
| **wal-g / pgBackRest** | Backup & restore (PITR) | Anything production-grade | Run as a sidecar/cron; configure WAL archiving |

## Tier 3 — situational, docs only

| Extension | Purpose | When |
|---|---|---|
| **pg_search / ParadeDB** | BM25 full-text + hybrid with pgvector | A workflow needs keyword AND vector retrieval together; pgvector alone isn't enough |
| **ZSON** | JSONB compression | Large volumes of JSONB and storage pressure |
| **hypopg** | Hypothetical indexes (tuning) | Query planning investigation |
| **pg_partman** | Time/id partitioning automation | Checkpoint/store tables grow large; partition for pruning |
| **PostGIS** | Geo | A workflow is explicitly geographic (not in our three target classes) |

## How to enable a Tier 2 extension

1. Add it to `docker/postgres.Dockerfile` **behind a build arg or a separate prod stage** so dev stays lean.
2. Add the `CREATE EXTENSION` line to a new `docker/extensions-tier2.sql`, run only in the prod compose.
3. Document the trigger in `docs/postgres-platform.md` so the next maintainer knows why it's there.
4. If the extension needs `shared_preload_libraries` (PGAudit), set it via the compose command or a custom `postgresql.conf`.

Example prod-only profile in `docker-compose.prod.yml`:
```yaml
services:
  postgres:
    build:
      context: docker
      dockerfile: postgres.Dockerfile
      args:
        INCLUDE_TIER2: "1"
    profiles: ["audit"]   # enabled with: docker compose --profile audit up
```
