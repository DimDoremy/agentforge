# Postgres image for agentforge — base pgvector image + Tier-1 extension binaries.
#
# The pgvector/pgvector:pg16 base image already ships pgvector AND has the PGDG
# apt repo configured, so the Tier-1 extension packages install directly:
#   - postgresql-16-cron  (pg_cron — scheduled dispatch)
#   - postgresql-16-pgmq  (pgmq   — in-DB task queue)
# pgai is best-effort (heavier; availability varies) — keep the build green if
# its package is absent; extensions.sql then degrades gracefully.
#
# See skills/postgres-as-platform/references/extension-bootstrap.md.

FROM pgvector/pgvector:pg16

# pg_cron + pgmq via PGDG (preconfigured in the base image).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-16-cron \
      postgresql-16-pgmq \
 && rm -rf /var/lib/apt/lists/*

# pgai: best-effort. Its package name/availability varies; if apt can't find it,
# the build still succeeds and extensions.sql WARNS (non-fatal). Python tools
# provide the fallback embedding path (references/pgai-in-db-llm.md).
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-16-pgai \
 && rm -rf /var/lib/apt/lists/* \
 || { echo "[postgres.Dockerfile] pgai package not found — degraded mode (non-fatal)"; }

# Extension bootstrap SQL, applied by entrypoint.sh once the DB is healthy.
COPY extensions.sql /docker/extensions.sql
