# request-shapes

## Table of Contents
1. [POST /runs/stream](#post-runsstream)
2. [POST /custom/invoke](#post-custominvoke)
3. [Passing extra parameters](#passing-extra-parameters)

## POST /runs/stream

The canonical "activate an agent" request.

```json
{
  "assistant_id": "research_summary",
  "input": {
    "messages": [
      { "role": "user", "content": "<the user-level prompt>" }
    ]
  },
  "stream_mode": "messages",
  "config": {
    "configurable": { "thread_id": "<optional-uuid>" }
  }
}
```

- `assistant_id` — **required**. Selects the agent from `langgraph.json` `graphs`.
- `input.messages` — the prompt. `role` is `"user"`/`"human"`; `content` is the text (or a content-parts list for multimodal).
- `stream_mode` — `"messages"` (token deltas), `"values"` (full state snapshots), `"updates"` (per-node diffs), or an array of these.
- `config.configurable.thread_id` — omit for a threadless run, or supply to continue a thread.

Response: server-sent events (SSE). Each event carries `(event, data)`. For `stream_mode="messages"`, data includes incremental message chunks and tool-call progress.

## POST /custom/invoke

```json
{
  "assistant_id": "research_summary",
  "message": "<the user-level prompt>",
  "thread_id": "<optional-uuid>"
}
```

Response (JSON, not streamed):
```json
{ "thread_id": "<uuid>", "message": "<final AI message text>" }
```

## Passing extra parameters

Don't encode tenant/user/locale in the message text. Pass structured params via LangGraph **context** (request-level):

```json
{
  "assistant_id": "customer_service",
  "input": { "messages": [ { "role": "user", "content": "where is my order?" } ] },
  "context": { "user_id": "u_123", "tenant": "acme", "locale": "zh-CN" }
}
```

Nodes read it via `runtime.context["user_id"]` (see [postgres-saver-store.md](../../postgres-as-platform/references/postgres-saver-store.md) for the store-from-node pattern). Keep `messages` purely conversational.
