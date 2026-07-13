# endpoints

## Table of Contents
1. [Custom endpoints](#custom-endpoints)
2. [Runtime endpoints](#runtime-endpoints)
3. [curl cookbook](#curl-cookbook)

## Custom endpoints

### GET /agents
Discovery — lists registered agents for UI pickers.

```bash
curl localhost:8000/agents
# -> [{"id":"research_summary","...":"..."}]
```

Implementation reads `registry.list_agents()`.

### POST /custom/invoke
One-shot JSON: send a message, get the final AI message back. Optional `thread_id` for continuity.

Request:
```json
{ "assistant_id": "research_summary",
  "message": "Research the graphite battery market and write a 1-page brief.",
  "thread_id": "optional-uuid" }
```
Response:
```json
{ "thread_id": "uuid",
  "message": "Here is a brief on the graphite battery market …" }
```

## Runtime endpoints

Mounted by `add_routes(app, get_runtime(), ...)`. The subset frontends care about:

| Method | Path | Purpose |
|---|---|---|
| POST | `/threads` | Create a thread (a conversation) |
| GET | `/threads/{thread_id}/state` | Inspect thread state |
| POST | `/runs/stream` | Run an assistant on a thread **with streaming** |
| POST | `/runs` | Run without streaming (returns final state) |
| GET | `/assistants` | List assistants (= graphs in `langgraph.json`) |

Full reference: LangGraph Platform docs.

## curl cookbook

### Stream a run (threadless)
```bash
curl -N -X POST localhost:8000/runs/stream \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"research_summary",
       "input":{"messages":[{"role":"user","content":"hello"}]},
       "stream_mode":"messages"}'
```

### Create a thread, then stream a run on it
```bash
THREAD=$(curl -s -X POST localhost:8000/threads | jq -r .thread_id)
curl -N -X POST localhost:8000/threads/$THREAD/runs/stream \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"research_summary",
       "input":{"messages":[{"role":"user","content":"remember: I prefer email"}]},
       "stream_mode":"messages"}'
```

### One-shot via the custom endpoint
```bash
curl -X POST localhost:8000/custom/invoke \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"research_summary","message":"hello"}'
```
