"""The Postgres platform layer — single DB, many capabilities.

This module is the **only** place that constructs Postgres-backed handles
(``PostgresSaver``, ``PostgresStore``, ``pgmq``, ``PGVector``). Agents and tools
obtain them via the ``get_*`` accessors; nothing should build its own connection
or read ``DB_DSN`` directly.

Design (see ``skills/postgres-as-platform/SKILL.md``):
    * one Postgres service, one DSN (``config.DB_DSN``);
    * lazy module-level singletons (constructed on first use);
    * :func:`setup_all` is idempotent and called once at startup.

The pgvector store (``get_vectorstore``) and pgai-dependent paths degrade
gracefully when an extension is unavailable — see the relevant references.
"""

from __future__ import annotations

import logging

from .config import get_settings

log = logging.getLogger(__name__)

# --- LangGraph persistence: checkpointer + long-term store ------------------

_saver = None
_store = None


def get_saver():
    """Return the singleton :class:`PostgresSaver` (thread/checkpoint memory)."""
    global _saver
    if _saver is None:
        from langgraph.checkpoint.postgres import PostgresSaver

        _saver = PostgresSaver.from_conn_string(get_settings().db_dsn)
    return _saver


def get_store():
    """Return the singleton :class:`PostgresStore` (cross-thread long-term memory)."""
    global _store
    if _store is None:
        from langgraph.store.postgres import PostgresStore

        _store = PostgresStore.from_conn_string(get_settings().db_dsn)
    return _store


# --- pgmq task queue ---------------------------------------------------------


def get_pgmq():
    """Return a singleton :class:`PGMQ` queue client (pgmq extension).

    Call :func:`ensure_queue` (from :func:`setup_all`) for the queues you need
    before sending. See ``references/pgmq-queue.md``.
    """
    global _pgmq
    if _pgmq is None:
        from tembo_pgmq_python import PGMQueue

        _pgmq = PGMQueue(url=get_settings().db_dsn)
    return _pgmq


_pgmq = None


def ensure_queue(name: str) -> None:
    """Create a pgmq queue if it does not already exist (idempotent)."""
    q = get_pgmq()
    try:
        existing = {row["queue_name"] for row in q.list_queues()}
    except Exception:  # list_queues shape varies across pgmq-python versions
        existing = set()
    if name not in existing:
        try:
            q.create_queue(name)
        except Exception as exc:  # pragma: no cover - race / already exists
            log.warning("ensure_queue(%s) could not create: %s", name, exc)


# --- pgvector RAG store ------------------------------------------------------


_vectorstore = None


def get_vectorstore():
    """Return a singleton LangChain ``PGVector`` store backed by pgvector.

    Constructed lazily; requires the ``vector`` extension (Tier 1, hard
    guarantee). Configure the embedding model + collection via env in a real
    project — the defaults here are illustrative.
    """
    global _vectorstore
    if _vectorstore is None:
        from langchain_openai import OpenAIEmbeddings
        from langchain_postgres import PGVector

        settings = get_settings()
        _vectorstore = PGVector(
            connection=settings.db_dsn,
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="kb",
            use_jsonb=True,
        )
    return _vectorstore


# --- pg_cron scheduling ------------------------------------------------------


def schedule_job(name: str, schedule_cron: str, sql: str) -> int | None:
    """Create or replace a pg_cron job that runs ``sql`` on ``schedule_cron``.

    Returns the jobid, or ``None`` if pg_cron is unavailable (Tier 1 but its
    presence depends on the image; non-fatal). See ``references/pg-cron-scheduling.md``.
    """
    import psycopg

    settings = get_settings()
    with psycopg.connect(settings.db_dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT cron.unschedule(%s)", (name,))  # idempotent replace
            try:
                cur.execute(
                    "SELECT cron.schedule_in_database(%s, %s, %s, current_user, %s)",
                    (name, schedule_cron, settings.db_name, sql),
                )
                row = cur.fetchone()
                return int(row[0]) if row else None
            except psycopg.Error as exc:
                log.warning("pg_cron schedule(%s) failed (extension missing?): %s", name, exc)
                return None


# --- one-shot setup ----------------------------------------------------------


def setup_all() -> None:
    """Idempotent startup: create LangGraph tables + default pgmq queues.

    Called by ``docker/entrypoint.sh`` after extensions.sql. Safe to re-run.
    Extension installation itself is handled by ``extensions.sql``, not here.
    """
    try:
        get_saver().setup()
    except Exception as exc:  # pragma: no cover - connection issues
        log.error("PostgresSaver.setup() failed: %s", exc)
        raise
    try:
        get_store().setup()
    except Exception as exc:  # pragma: no cover
        log.warning("PostgresStore.setup() failed (non-fatal): %s", exc)
    # Create the default queue the publishing pattern expects; add more as needed.
    try:
        ensure_queue("publish_jobs")
    except Exception as exc:  # pragma: no cover - pgmq missing
        log.warning("ensure_queue('publish_jobs') failed (pgmq missing?): %s", exc)
