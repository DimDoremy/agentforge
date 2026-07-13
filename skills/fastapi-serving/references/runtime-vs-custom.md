# runtime-vs-custom

## Table of Contents
1. [Two surfaces, one app](#two-surfaces-one-app)
2. [When to use which](#when-to-use-which)
3. [Mounting the runtime](#mounting-the-runtime)

## Two surfaces, one app

`app/main.py` builds one FastAPI app and exposes two surfaces:

```python
from fastapi import FastAPI
from langgraph_platform import get_runtime  # or the SDK's add_routes helper
from langgraph_sdk import get_runtime as add_routes  # actual import per your langgraph-cli version

app = FastAPI(title="agentforge")

# (1) Full LangGraph runtime: /threads, /runs/stream, ...
add_routes(app, ...)            # see "Mounting the runtime" below

# (2) Custom convenience endpoints
@app.get("/agents")             # discovery
@app.post("/custom/invoke")     # one-shot JSON
```

The runtime owns the hard problems (streaming, thread persistence, interrupts). The custom endpoints own only the convenience cases.

## When to use which

| Frontend need | Surface | Why |
|---|---|---|
| Live token streaming (chat UI) | runtime `/runs/stream` | Server-sent events, incremental deltas |
| Multi-turn conversation with memory | runtime `/threads` + `/runs/stream` | Thread/checkpointer continuity |
| Resume after human-in-the-loop | runtime interrupt APIs | First-class support |
| "Show me which agents exist" | custom `/agents` | Thin listing from registry |
| Simple POST → final answer JSON | custom `/custom/invoke` | No stream parsing on the client |
| Batch / cron-triggered run | runtime `/runs` (non-stream) or `/custom/invoke` | Either; `/runs` if you still want thread tracking |

Rule: default to the runtime. Add a custom endpoint only when the runtime shape is awkward for the consumer.

## Mounting the runtime

The exact import path depends on the installed `langgraph-cli`/`langgraph-platform` version. The skeleton's `app/main.py` is the source of truth; conceptually:

```python
from langgraph.runtime import get_runtime
runtime = get_runtime()                 # reads langgraph.json
runtime.add_routes(app)                 # mounts /threads, /runs/*, /assistants, etc.
```

If your version exposes `add_routes` as a free function instead, use that. Keep the call in the factory so test clients and the real server see the same routes.
