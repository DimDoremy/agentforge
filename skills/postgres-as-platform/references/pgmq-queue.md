# pgmq-queue

## Table of Contents
1. [Why pgmq](#why-pgmq)
2. [Prerequisites](#prerequisites)
3. [The queue handle](#the-queue-handle)
4. [Send / read / archive](#send--read--archive)
5. [Worker loop](#worker-loop)
6. [Multi-platform publish pattern](#multi-platform-publish-pattern)

## Why pgmq

pgmq is an SQS/RSMQ-style message queue **inside Postgres**. For workflow-level throughput it is more than enough, and it gives you a single ACID boundary: enqueue a job in the same transaction as the business write, and they commit or roll back together. No Redis, no Celery broker.

Reach for a dedicated broker **only** when sustained throughput exceeds a few thousand messages/second (rare at this scale).

## Prerequisites

- `pgmq` extension present (Tier 1). `extensions.sql` does `CREATE EXTENSION IF NOT EXISTS pgmq;` idempotently.
- The `pgmq` Python client (`tembo-pgmq-python` in `pyproject.toml`; imports as `tembo_pgmq_python`). Note: PyPI's standalone `pgmq` package is a *different* asyncpg-based library — use `tembo-pgmq-python` for the PGMQ Postgres extension.

## The queue handle

In `platform.py`:
```python
from pgmq import PGMQueue
from .config import settings

_pgmq: PGMQueue | None = None


def get_pgmq() -> PGMQueue:
    global _pgmq
    if _pgmq is None:
        _pgmq = PGMQueue(url=settings.DB_DSN)
    return _pgmq


def ensure_queue(name: str) -> None:
    q = get_pgmq()
    if name not in {q.row["queue_name"] for q in q.list_queues()}:
        q.create_queue(name)
```

Call `ensure_queue("publish_jobs")` from `setup_all()` for queues the harness always needs.

## Send / read / archive

```python
q = get_pgmq()
q.send("publish_jobs", {"platform": "twitter", "content": "…", "run_at": "..."})

msg = q.read("publish_jobs")          # -> Message(msg_id, message, read_ct, …) or None
q.archive("publish_jobs", msg.msg_id) # acknowledge (keeps history); q.delete(...) to drop
```

Visibility timeout / VT lets you requeue if a worker dies mid-job:
```python
q.send("publish_jobs", payload, delay=300)   # visible after 300s
```

## Worker loop

A worker is a small async loop (its own process, e.g. a second compose service or an `uv run` script):
```python
import asyncio
from <pkg>.platform import get_pgmq

async def worker(queue="publish_jobs"):
    q = get_pgmq()
    while True:
        msg = q.read(queue)
        if msg is None:
            await asyncio.sleep(1); continue
        try:
            await handle(msg.message)   # your platform-publish logic
            q.archive(queue, msg.msg_id)
        except Exception:
            # leave un-archived; it reappears after VT
            ...
```

## Multi-platform publish pattern

Fan-out publish, idempotent and recoverable:
1. Agent's `@tool` `enqueue_publish(platforms, content)` → one `pgmq.send` per platform (transactional with the "scheduled post" row).
2. Worker reads jobs, calls each platform's HTTP API (in **Python**, never from the DB), archives on success.
3. Crash mid-publish → job reappears after VT → ensure your platform call is idempotent (use a client-side publish id).

See [pg-cron-scheduling.md](pg-cron-scheduling.md) for the "cron → enqueue" half of this pattern.
