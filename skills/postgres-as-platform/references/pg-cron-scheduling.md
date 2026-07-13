# pg-cron-scheduling

## Table of Contents
1. [What pg_cron is for here](#what-pg_cron-is-for-here)
2. [Prerequisites & gotchas](#prerequisites--gotchas)
3. [The cron handle](#the-cron-handle)
4. [Cron → pgmq pattern](#cron--pgmq-pattern)
5. [Listing / unscheduling](#listing--unscheduling)

## What pg_cron is for here

Timed workflow triggers — most obviously **scheduled multi-platform publishing** ("post this at 09:00 across 3 platforms"). pg_cron runs cron jobs **inside Postgres**, so you don't need a separate scheduler (no APScheduler, no k8s CronJob) and the schedule lives next to the data it acts on.

## Prerequisites & gotchas

- `pg_cron` extension present (Tier 1, installed via `apt` in `postgres.Dockerfile`).
- **Critical pg_cron constraint:** it needs `cron.database_name` set to your DB in `postgresql.conf`, and the extension must be created in that DB. `entrypoint.sh` handles this before `langgraph` starts.
- pg_cron runs as the DB role that created the job — give that role only the privileges the scheduled SQL needs (least privilege).
- pg_cron schedules server-side UTC by default; set `cron.timezone` in `postgresql.conf` if you need local time.

## The cron handle

pg_cron has no first-class Python client; wrap the SQL. In `platform.py`:
```python
from .persistence_conn import get_conn   # a psycopg connection from the same DSN

def schedule(name: str, schedule_cron: str, sql: str) -> int:
    """Create or replace a cron job that runs `sql`. Returns the jobid."""
    with get_conn() as cur:
        cur.execute("SELECT cron.unschedule(%s)", (name,))  # idempotent replace
        cur.execute(
            "SELECT cron.schedule_in_database(%s, %s, %s, %s, %s)",
            (name, schedule_cron, settings.DB_NAME, settings.DB_ROLE, sql),
        )
        return cur.fetchone()[0]
```

Use `cron.schedule_in_database(...)` (not `cron.schedule`) so you can target the correct DB explicitly.

## Cron → pgmq pattern

pg_cron should **not** do heavy work itself. Its job is to enqueue into pgmq; the worker (see [pgmq-queue.md](pgmq-queue.md)) does the actual publishing:

```sql
-- scheduled every minute; enqueues any due posts
SELECT pgmq.send('publish_jobs', jsonb_build_object(
  'post_id', p.id, 'platform', p.platform, 'content', p.content
))
FROM scheduled_posts p
WHERE p.run_at <= now() AND p.status = 'pending';
```

A `@tool` for the agent:
```python
@tool
def schedule_post(post_id: int, run_at: str) -> str:
    """Schedule a draft post to be published at run_at (ISO8601)."""
    # update scheduled_posts row; the cron-enqueue SQL above picks it up
    ...
```

Benefits: the schedule survives app restarts (it's in the DB); the worker is the only thing doing HTTP egress; failures are recoverable via pgmq visibility timeout.

## Listing / unscheduling

```sql
SELECT jobid, schedule, command, active FROM cron.job;
SELECT cron.unschedule('<name>');   -- or by jobid
```
