# tech-stack

## Table of Contents
1. [The stack at a glance](#the-stack-at-a-glance)
2. [Role of each component](#role-of-each-component)
3. [Why these choices](#why-these-choices)
4. [Versions & pinning](#versions--pinning)

## The stack at a glance

| Layer | Component | Role |
|---|---|---|
| Env / deps | **uv** | Fast Python package manager; single `pyproject.toml` + committed `uv.lock` for reproducibility |
| Runtime (in container) | **docker-compose** | Two standalone files: `docker-compose.dev.yml` (reload, source mount) and `docker-compose.prod.yml` (built image, restart policy) |
| Web framework | **FastAPI** | Custom endpoints (`/agents`, `/custom/invoke`) + mounts the LangGraph runtime |
| Agent runtime | **LangGraph Platform runtime** (`langgraph dev` / `up`) | Serves compiled graphs at `/threads`, `/runs/stream`, …; Postgres-backed persistence |
| Agent orchestration | **LangGraph** | State graphs, checkpointing, streaming primitives |
| Agent authoring | **DeepAgents** | `create_deep_agent(...)` is the default agent body (planning/todo, subagents, skills middleware, FilesystemBackend) |
| LLM abstraction | **LangChain** | `init_chat_model`, `@tool`, document loaders, prompts |
| Persistence / queue / vector / schedule | **Postgres (+ extensions)** | Single service: `PostgresSaver` + `PostgresStore` + `pgvector` + `pgai` + `pgmq` + `pg_cron` |

## Role of each component

- **uv** — sole source of truth for deps. `uv sync` creates `.venv` from `pyproject.toml` + `uv.lock`. Never mix in pip/poetry.
- **docker-compose** — `postgres` + `agent` services only (Tier 1 extensions baked into the postgres image). No Redis, no broker, no vector DB.
- **FastAPI** — a thin app (`app/main.py`) that (a) calls `add_routes(app, get_runtime(), ...)` to mount the full LangGraph runtime, and (b) adds convenience endpoints. It is **not** a hand-rolled reimplementation of the runtime.
- **LangGraph Platform runtime** — `langgraph dev` (local) / `langgraph up` (deploy). Reads `langgraph.json`, serves every registered graph. This is the primary way agents are reached (`POST /runs/stream`).
- **LangGraph** — the graph primitives; also `PostgresSaver` (checkpointer) and `PostgresStore` (long-term memory).
- **DeepAgents** — `create_deep_agent(model, tools, memory, skills, backend, checkpointer, store)` returns a compiled graph; that graph is what gets registered. Tools = workflow steps.
- **LangChain** — `init_chat_model(model=<string>)` makes the provider pluggable (swap via `.env` `MODEL=`); `@tool` defines steps.
- **Postgres extensions** — see [postgres-as-platform](../../postgres-as-platform/SKILL.md). One DB, many capabilities.

## Why these choices

- **LangGraph runtime over hand-rolled FastAPI** — batteries-included: threads, streaming, persistence, studio. A custom FastAPI app only adds the few convenience endpoints.
- **DeepAgents as the agent body** — gives planning/todo, skills middleware (same SKILL.md format as lerdrail), and subagents for free, while still producing a plain LangGraph graph that the runtime serves.
- **Single Postgres** — collapses the compose stack; transactional queue, RAG, and scheduling share one DB and one ACID boundary. Sufficient for workflow-level throughput.
- **uv over pip/poetry** — dramatically faster, lockfile-first, the modern default.

## Versions & pinning

- Python: target **3.12** in the image (3.14 is too new for some wheels; 3.12 is the safe LangGraph target). The host has 3.14 but the image pins 3.12.
- Deps are pinned in `pyproject.toml` and locked in `uv.lock` (committed). `uv sync --frozen` in prod.
- Extension versions ride the `pgvector/pgvector:pg16` base image; Tier-1 extras installed via `apt` in `docker/postgres.Dockerfile`.
