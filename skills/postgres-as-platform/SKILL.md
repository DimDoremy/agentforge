---
name: postgres-as-platform
description: Use when deciding where a persistence, memory, queue, vector/RAG, scheduling, or in-DB LLM capability should live in an agentforge project — i.e. choosing between a Postgres extension (pgvector / pgai / pgmq / pg_cron) and an external service (Redis, Celery, a vector DB, a scheduler), or wiring PostgresSaver/PostgresStore. Owns the single-Postgres principle, the Tier 1/2/3 extension model, the decision matrix, the extension-bootstrap conventions, and the container-vs-host networking rules. Delegates HTTP serving to fastapi-serving, agent authoring to deepagent-authoring.
---

# postgres-as-platform

## Overview

**If a capability can be provided by a Postgres extension, use the Postgres extension — do not introduce a third service.** This collapses the compose stack to **one Postgres service** (no Redis, no vector DB, no standalone broker/scheduler) and gives the workflow a single ACID boundary.

This skill owns the **decision** of where a capability lives and the **wiring conventions** for the Postgres platform layer (`platform.py`). It does not own agent authoring or HTTP shapes.

## The single-Postgres principle

The harness runs **one** Postgres service. Everything below is a capability *of that service*:

| Capability | Provided by | LangGraph/LangChain surface |
|---|---|---|
| Short-term conversation memory (per thread) | `PostgresSaver` (built-in tables) | `checkpointer=get_saver()` |
| Long-term memory (cross-thread facts) | `PostgresStore` (built-in tables) | `store=get_store()` |
| Vector storage / similarity search (RAG) | **pgvector** | `PGVector` (langchain-postgres) via `get_vectorstore()` |
| In-DB LLM calls / auto-embeddings | **pgai** (Vectorizer) | SQL; invoked from tools |
| Task queue / fan-out | **pgmq** | `pgmq-python` via `get_pgmq()` |
| Scheduled dispatch (e.g. timed publishing) | **pg_cron** | SQL `cron.schedule`; from tools via `get_cron()` |

All five share one DB, one DSN (`config.DB_DSN`), one set of credentials.

## Tier model

### Tier 1 — core, installed in dev AND prod

| Extension | Workflow class it serves | Notes |
|---|---|---|
| `pgvector` | All (RAG) | Vector type + HNSW/IVFFlat. **Hard guarantee** — base image ships it. |
| `pgai` | All | In-DB LLM/embedding; Vectorizer auto-syncs embeddings. **Best-effort** — heavier; may be unavailable on some images (non-fatal). |
| `pgmq` | Multi-platform publish (queue/fan-out) | SQS-style in-DB queue, transactional. |
| `pg_cron` | Multi-platform publish (timed dispatch) | DB-side cron; pairs with pgmq (cron → enqueue → worker). |

### Tier 2 — prod/compliance, opt-in (docs; not installed by default)

- **PgBouncer** — connection pooling when the agent opens many connections.
- **PostgreSQL Anonymizer** — PII masking/redaction (customer-research compliance).
- **PGAudit / pgMemento** — audit logging for customer data.
- **wal-g / pgBackRest** — backup/restore for production.

See [references/extension-tiers.md](references/extension-tiers.md) for when to enable each.

### Tier 3 — situational, docs only

- **pg_search / ParadeDB** — BM25 hybrid retrieval when a workflow needs keyword + vector search together.
- **ZSON / hypopg / pg_partman** — JSONB compression, index tuning, partitioning at scale.

## Decision matrix

When adding a capability, pick the default; escalate only when the condition holds.

| Need | Default | Escalate when… |
|---|---|---|
| Scheduled workflow trigger | `pg_cron` → `pgmq` | — |
| Short-term conversation memory | `PostgresSaver` | — |
| Cross-thread long-term memory | `PostgresStore` | — |
| Vector retrieval / RAG | `pgvector` (+ `PGVector`) | need BM25 hybrid → Tier 3 `pg_search` |
| In-DB LLM / embeddings | `pgai` (Vectorizer) | strong preference for an external pipeline → demote to a Python `@tool` |
| Task queue / async fan-out | `pgmq` | throughput > a few thousand msg/s sustained → consider a dedicated broker (rare for workflow-level) |
| Connection management | direct connect | prod load arrives → Tier 2 `PgBouncer` |
| Customer PII | plain columns | compliance requires it → Tier 2 `PostgreSQL Anonymizer` |
| Outbound HTTP (to social platforms etc.) | Python `@tool` (httpx) | **never** try to push HTTP out of the DB |

> Rule of thumb: reach for Tier 2/3 only with a concrete trigger, never "just in case". This pack's default is Tier 1 + the built-in LangGraph savers.

## How this skill relates to other layers

- The **mechanics** of defining a `@tool` that uses pgvector/pgmq/pg_cron → [deepagent-authoring](../deepagent-authoring/SKILL.md) + [references/pgvector-rag.md](references/pgvector-rag.md) etc.
- The **HTTP surface** that exposes agents (which depend on this platform) → [fastapi-serving](../fastapi-serving/SKILL.md).
- The **bootstrap** (image, `extensions.sql`, entrypoint ordering) → [references/extension-bootstrap.md](references/extension-bootstrap.md).

## Quick reference

| Want to… | Read |
|---|---|
| Wire checkpointer + long-term store | [references/postgres-saver-store.md](references/postgres-saver-store.md) |
| Add RAG / vector retrieval to an agent | [references/pgvector-rag.md](references/pgvector-rag.md) |
| Call an LLM or auto-embed from SQL | [references/pgai-in-db-llm.md](references/pgai-in-db-llm.md) |
| Add a task queue / fan-out step | [references/pgmq-queue.md](references/pgmq-queue.md) |
| Schedule a workflow (e.g. timed publish) | [references/pg-cron-scheduling.md](references/pg-cron-scheduling.md) |
| Decide on a Tier 2/3 extension | [references/extension-tiers.md](references/extension-tiers.md) |
| Understand container-vs-host DB addresses | [references/networking-rules.md](references/networking-rules.md) |
| How extensions get installed in the image | [references/extension-bootstrap.md](references/extension-bootstrap.md) |

## Common mistakes

| Mistake | Fix |
|---|---|
| Adding Redis/Celery "for the queue" | Use `pgmq` — same DB, transactional, see [references/pgmq-queue.md](references/pgmq-queue.md) |
| Putting `127.0.0.1` in `DB_DSN` for the container | Inside compose the host is the **service name** `postgres`; `127.0.0.1` is only for host-side tools. See [references/networking-rules.md](references/networking-rules.md) |
| Calling `PostgresSaver.setup()` per request | Call once at startup (`platform.setup_all()`); reuse the singleton |
| Treating pgai absence as fatal | pgai is best-effort; degrade to a Python `@tool` embedding step. See [references/pgai-in-db-llm.md](references/pgai-in-db-llm.md) |
| Forgetting to `CREATE EXTENSION` for pgmq/pg_cron | `extensions.sql` does this idempotently at startup; verify with `\dx` |
| Trying to make Postgres call outbound HTTP to social platforms | Keep outbound HTTP in Python tools; Postgres stores/queues, it doesn't egress |
