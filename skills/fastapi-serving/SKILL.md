---
name: fastapi-serving
description: Use when exposing agentforge agents over HTTP — wiring the LangGraph Platform runtime into a FastAPI app, adding custom endpoints (GET /agents, POST /custom/invoke), or defining the request/response shapes that external frontends POST to. Owns the runtime-vs-custom-endpoint split, the endpoint catalog, and the activation contract (how a user prompt + params reaches a registered agent). Delegates persistence/queue to postgres-as-platform, agent construction to deepagent-authoring.
---

# fastapi-serving

## Overview

Agents built with `create_deep_agent` are plain compiled LangGraph graphs. They are exposed over HTTP two ways, both living in one FastAPI app (`app/main.py`):

1. **LangGraph Platform runtime** (mounted via `add_routes`) — the full surface: `/threads`, `/runs/stream`, `/runs`, etc. This is the **primary** way frontends reach an agent, and the one that gives streaming for free.
2. **Custom convenience endpoints** — `GET /agents` (discovery) and `POST /custom/invoke` (simple fire-and-forget JSON).

The app is a thin layer; it does **not** reimplement the runtime.

## The runtime-vs-custom split

| Need | Use |
|---|---|
| Stream tokens/tool events to a frontend | `POST /runs/stream` (runtime) |
| Create/list/resume threads | `/threads*` (runtime) |
| Human-in-the-loop interrupts | runtime interrupt APIs |
| "List what agents exist" for a UI picker | `GET /agents` (custom) |
| One-shot JSON request → final answer, no streaming | `POST /custom/invoke` (custom) |

Details: [references/runtime-vs-custom.md](references/runtime-vs-custom.md).

## Endpoint catalog

See [references/endpoints.md](references/endpoints.md) for the full list with examples. Minimal:

- `GET /agents` → `[{ "id": "<name>", ... }]` from `registry.list_agents()`.
- `POST /custom/invoke` body `{assistant_id, message, thread_id?}` → `{thread_id, message}`.
- Runtime endpoints under `/` via `add_routes(app, get_runtime(), ...)`.

## Activation contract

A user prompt reaches an agent like this (full shapes in [references/request-shapes.md](references/request-shapes.md)):

```
POST /runs/stream
{ "assistant_id": "<name>",
  "input": { "messages": [ {"role":"user","content":"<the user prompt>"} ] },
  "stream_mode": "messages" }        # or "values"/"updates"/"messages-tuple"
```

`assistant_id` selects the agent from `langgraph.json`'s `graphs`. Extra parameters (e.g. tenant, user id) travel via LangGraph's `context` (configured per request), not by stuffing them into `messages`.

## How this skill relates to other layers

- **Which agents exist** to be served → `langgraph.json` + `registry.py` (see [harness-core](../harness-core/SKILL.md)).
- **How an agent is built** (tools/skills/memory) → [deepagent-authoring](../deepagent-authoring/SKILL.md).
- **Persistence** behind `/threads` → [postgres-as-platform](../postgres-as-platform/SKILL.md).

## Quick reference

| Want to… | Read |
|---|---|
| Decide runtime vs custom endpoint | [references/runtime-vs-custom.md](references/runtime-vs-custom.md) |
| See all endpoints + curl examples | [references/endpoints.md](references/endpoints.md) |
| Exact request/response JSON shapes | [references/request-shapes.md](references/request-shapes.md) |

## Common mistakes

| Mistake | Fix |
|---|---|
| Hand-rolling `/invoke` + `/stream` instead of mounting the runtime | Use `add_routes(app, get_runtime(), ...)`; only add `/custom/invoke` as a convenience |
| Stuffing user/tenant params into the message text | Pass them via LangGraph `context` (request-level config), keep `messages` clean |
| Forgetting `assistant_id` in `/runs/stream` | It's required — it's the key into `graphs` |
| Hardcoding the model/provider in the app | The app never touches the model; agents do, via `get_model()` |
| Returning the whole state when the frontend wants the final message | `/custom/invoke` extracts the last AI message; for richer data use the runtime |
