#!/usr/bin/env sh
# agent service entrypoint — runs inside the `agent` compose service.
#
# Ordering (see skills/postgres-as-platform/references/extension-bootstrap.md):
#   1. wait for Postgres readiness (service-name host)
#   2. apply extensions.sql (Tier-1 extensions, idempotent)
#   3. run platform.setup_all() (LangGraph tables + default pgmq queues)
#   4. hand off to the runtime command (langgraph dev/up)
set -eu

: "${DB_DSN:?DB_DSN must be set}"
: "${DB_NAME:=agentforge}"

echo "[entrypoint] waiting for postgres on service host ..."
# Extract host from DB_DSN for pg_isready (DSN looks like postgresql://u:p@HOST:5432/db).
PG_HOST=$(printf '%s' "$DB_DSN" | sed -E 's#^[^@]*@([^:/]+).*#\1#')
until pg_isready -h "$PG_HOST" -U "${DB_USER:-postgres}" >/dev/null 2>&1; do
    echo "[entrypoint] postgres not ready, retrying in 1s ..."
    sleep 1
done
echo "[entrypoint] postgres ready."

# 2. Apply Tier-1 extensions (idempotent; pgai failure is non-fatal).
echo "[entrypoint] applying extensions.sql ..."
psql "$DB_DSN" -v ON_ERROR_STOP=1 -f /app/docker/extensions.sql || {
    echo "[entrypoint] WARNING: extensions.sql had failures — continuing (pgai best-effort)."
}

# 3. LangGraph tables + default queues.
echo "[entrypoint] platform.setup_all() ..."
uv run python -c "from agentforge_template.platform import setup_all; setup_all()" || {
    echo "[entrypoint] WARNING: platform.setup_all() failed — the runtime will still start; fix before relying on persistence."
}

# 4. Hand off to the image CMD (langgraph dev / up).
echo "[entrypoint] handing off to: $*"
exec "$@"
