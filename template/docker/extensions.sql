-- Tier-1 extensions for agentforge. Idempotent. Applied by entrypoint.sh once
-- the DB is healthy. See skills/postgres-as-platform/references/extension-bootstrap.md.

-- pgvector: HARD GUARANTEE (base image ships it). RAG foundation.
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_cron: scheduled dispatch (multi-platform publish). Requires
-- shared_preload_libraries='pg_cron' (set in compose command) + cron.database_name.
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- pgmq: in-DB task queue. The extension creates the 'pgmq' schema.
CREATE EXTENSION IF NOT EXISTS pgmq;

-- pgai: BEST-EFFORT (heavier; may be absent). Non-fatal — workflows fall back
-- to a Python @tool embedding step. See references/pgai-in-db-llm.md.
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS pgai;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'pgai not available (degraded mode): %', SQLERRM;
END $$;
