# HTTP API

Two surfaces share one FastAPI app (`template/src/<pkg>/app/main.py`):

1. **LangGraph Platform runtime** — mounted via `add_routes`; the primary path.
2. **Custom convenience endpoints** — `/agents`, `/custom/invoke`, `/health`.

## Custom endpoints

### GET /agents
Discovery — lists registered agents.

```bash
curl localhost:8000/agents
# []                           # skeleton: empty registry
# [{"id":"research_summary"}]  # after adding an agent
```

### POST /custom/invoke
One-shot JSON: message in, final AI message out.

```bash
curl -X POST localhost:8000/custom/invoke \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"research_summary",
       "message":"Research the graphite battery market."}'
# {"thread_id":"…","message":"Here is a brief …"}
```

Request:
```json
{ "assistant_id": "<name>", "message": "<prompt>", "thread_id": "<optional uuid>" }
```
Response: `{ "thread_id": "<uuid>", "message": "<final AI message>" }`.
Unknown `assistant_id` → `404` with the list of known ids.

### GET /health
`{"status":"ok"}` — liveness probe.

## Runtime endpoints (primary)

Mounted by `add_routes(app, …)`. The subset frontends use most:

| Method | Path | Purpose |
|---|---|---|
| POST | `/threads` | create a thread (conversation) |
| GET | `/threads/{id}/state` | inspect thread state |
| POST | `/runs/stream` | run an assistant **with streaming** (SSE) |
| POST | `/runs` | run without streaming (returns final state) |
| GET | `/assistants` | list assistants (= graphs in `langgraph.json`) |

### Activate an agent (streaming)

```bash
curl -N -X POST localhost:8000/runs/stream \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"research_summary",
       "input":{"messages":[{"role":"user","content":"hello"}]},
       "stream_mode":"messages"}'
```

### Continue a thread

```bash
THREAD=$(curl -s -X POST localhost:8000/threads | jq -r .thread_id)
curl -N -X POST localhost:8000/threads/$THREAD/runs/stream \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"research_summary",
       "input":{"messages":[{"role":"user","content":"remember: I prefer email"}]},
       "stream_mode":"messages"}'
```

## Passing structured params

Don't encode tenant/user/locale in the message text. Use LangGraph **context**:
```json
{ "assistant_id":"customer_service",
  "input":{"messages":[{"role":"user","content":"where is my order?"}]},
  "context":{"user_id":"u_123","tenant":"acme","locale":"zh-CN"} }
```
Nodes read it via `runtime.context`. See
[`skills/fastapi-serving/references/request-shapes.md`](../skills/fastapi-serving/references/request-shapes.md).

## Verified

`/agents`, `/health`, `/custom/invoke` (incl. 404 path) are verified via uvicorn +
curl in a no-DB / no-LLM-key environment. The runtime endpoints come alive once
the container (`langgraph dev`/`up`) provides the runtime.
