# Architecture

> agentforge = a reusable harness-engineering pack for **workflow-level** AI agents
> (AI customer-service, customer research, multi-platform publishing, …), on
> FastAPI + LangChain + LangGraph + DeepAgents, with uv for env management and
> docker-compose (split dev/prod) for runtime.

## The two layers

```
agentforge/
├── skills/      ← Layer A: lerdrail-style skill pack (the core deliverable)
└── template/    ← Layer B: runnable code skeleton (a new project's starting point)
```

- **Layer A — `skills/`** is project-agnostic. Five skills encode the conventions;
  each `SKILL.md` has YAML front-matter (`name` + a `description` trigger beginning
  with "Use when…") and pushes detail into sibling `references/*.md` loaded on
  demand (progressive disclosure, to control token cost). This is exactly lerdrail's
  shape.
- **Layer B — `template/`** is a minimal but fully wired Python package + Docker setup.
  Copy it to start a new project; the skills describe how to instantiate and extend.

Every agent in this harness is **one `create_deep_agent(...)` instance** — that
compiled graph is what gets registered in `langgraph.json` and served.

## Runtime architecture (Layer B running)

```
External frontend / curl ──POST──► FastAPI app (app/main.py)
                                     │  GET /agents, POST /custom/invoke, GET /health
                                     │  + add_routes(...) mounts the LangGraph runtime:
                                     │     /threads, /runs/stream, /runs, /assistants
                                     ▼
                          registry.AGENTS: { name → compiled graph }
                                     │ each graph built with create_deep_agent(...)
                                     ▼
   ┌───────────────────────────────────────────────────────────────┐
   │  Postgres — the single infrastructure service                 │
   │  ├─ PostgresSaver   (checkpointer: per-thread state)          │
   │  ├─ PostgresStore   (cross-thread long-term memory)           │
   │  ├─ pgvector        (vector store / RAG)                      │
   │  ├─ pgai            (in-DB LLM / auto-embedding, best-effort) │
   │  ├─ pgmq            (task queue / fan-out)                    │
   │  └─ pg_cron         (scheduled dispatch)                      │
   └───────────────────────────────────────────────────────────────┘
```

## The single-Postgres principle

**If a capability can be provided by a Postgres extension, use it — do not add a
third service.** The compose stack therefore has exactly two services
(`postgres` + `agent`), no Redis / vector DB / broker / scheduler. This gives the
workflow one ACID boundary and minimal operational surface. See
[`postgres-platform.md`](postgres-platform.md).

## Why these choices

- **LangGraph Platform runtime** (mounted via `add_routes`) over a hand-rolled
  server — threads, streaming, persistence, interrupts are free.
- **DeepAgents as the agent body** — planning/todo, skills middleware (same
  SKILL.md format as lerdrail), subagents, FilesystemBackend; still produces a
  plain LangGraph graph the runtime can serve.
- **uv over pip/poetry** — fast, lockfile-first.
- **Two standalone compose files** — readability over DRY; each env is fully
  self-contained.

## Verified vs. environment-blocked

- ✅ `uv sync` resolves (265 packages); `uv run pytest` green (6 tests);
  end-to-end HTTP smoke (`/agents` → `[]`, `/health`, `/custom/invoke` 404) via uvicorn.
- ✅ `langgraph validate` reads `langgraph.json` correctly (warns only about the
  intentionally-empty `graphs`, as designed for the skeleton).
- ⚠️ `docker build` / `docker compose up` **not run in this environment** — the
  sandbox has no Docker Hub access (registry-1.docker.io unreachable on v4/v6).
  The Dockerfiles use the officially-documented install paths
  (`pgvector/pgvector:pg16` + `apt-get postgresql-16-cron` / `postgresql-16-pgmq`
  from the preconfigured PGDG repo). Run `docker compose -f docker-compose.dev.yml up`
  in an environment with registry access to verify the Tier-1 extensions land.
