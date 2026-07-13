# postgres-saver-store

## Table of Contents
1. [Checkpointer vs Store — one sentence](#checkpointer-vs-store--one-sentence)
2. [Wiring in platform.py](#wiring-in-platformpy)
3. [setup() ordering](#setup-ordering)
4. [Using the store from a node](#using-the-store-from-a-node)

## Checkpointer vs Store — one sentence

- **`PostgresSaver`** (checkpointer) — snapshots of a single thread's graph state: conversation continuity, human-in-the-loop, time travel, fault tolerance. LangGraph wires it automatically.
- **`PostgresStore`** — cross-thread key/value memory: user preferences, facts, shared knowledge. You read/write it explicitly.

Both come from the same `config.DB_DSN`.

## Wiring in platform.py

Single connection string, lazy singletons, one `setup_all()`:

```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from .config import settings

_saver: PostgresSaver | None = None
_store: PostgresStore | None = None


def get_saver() -> PostgresSaver:
    global _saver
    if _saver is None:
        _saver = PostgresSaver.from_conn_string(settings.DB_DSN)
    return _saver


def get_store() -> PostgresStore:
    global _store
    if _store is None:
        _store = PostgresStore.from_conn_string(settings.DB_DSN)
    return _store


def setup_all() -> None:
    """Idempotent. Call once at startup (entrypoint) before serving."""
    get_saver().setup()
    get_store().setup()
```

Then in `create_deep_agent(...)`:
```python
graph = create_deep_agent(
    model=get_model(),
    tools=[...],
    checkpointer=get_saver(),
    store=get_store(),
    ...
)
```

## setup() ordering

`setup()` creates tables/indexes. Run it **once** after the DB is healthy and **before** the runtime serves traffic. `docker/entrypoint.sh` guarantees this order: wait-for-pg → `extensions.sql` → `setup_all()` → `langgraph dev`/`up`. `setup()` is idempotent, so re-running on restart is safe.

## Using the store from a node

The store is reached via the runtime context inside a node (LangGraph ≥ recent versions), or by injecting the store singleton:

```python
from langgraph.store.base import BaseStore
from langgraph.runtime import Runtime
from .platform import get_store

def remember(state, runtime: Runtime):
    store = runtime.store          # injected by the graph's store=
    user_id = runtime.context["user_id"]
    store.put(("memories", user_id), key="<uuid>", value={"data": "user prefers email"})
```

Namespacing convention: `("<concept>", "<scope_id>")`, e.g. `("memories", user_id)` or `("kb", tenant_id)`.
