---
name: harness-core
description: Use at the START of any task that builds, extends, or explains an agent harness in an agentforge project — i.e. the reusable pack for workflow-level AI agents on FastAPI + LangChain + LangGraph + DeepAgents (uv-managed, docker-compose split dev/prod, single-Postgres with pgvector/pgai/pgmq/pg_cron). Owns the technology-stack overview, the two-layer structure (skills/ pack + template/ skeleton), the fixed 3-step recipe for adding a new agent, and the cross-skill routing rules. Delegates persistence/queue/vector/scheduling specifics to the postgres-as-platform skill, HTTP serving to fastapi-serving, agent authoring to deepagent-authoring, and the development lifecycle to dev-workflow.
---

# harness-core

## Overview

`agentforge` is a **reusable harness-engineering pack**, not a single demo app. It targets **workflow-level agents** — concrete, repeatable business flows like AI customer service, customer research, and multi-platform publishing — not general-purpose autonomous agents.

It has two layers:

- **层 A — `skills/` (the core deliverable):** five lerdrail-style skills (this file + `postgres-as-platform` + `fastapi-serving` + `deepagent-authoring` + `dev-workflow`). Each `SKILL.md` has YAML front-matter `name` + a `description` trigger ("Use when…"); details live in sibling `references/*.md` loaded on demand (progressive disclosure, to control token cost).
- **层 B — `template/`:** a minimal, runnable code skeleton (`uv sync` / `docker compose` / `pytest` all green). New projects start here; the skills describe how to instantiate and extend it.

Every agent in this harness is one `create_deep_agent(...)` instance. A workflow's steps/branches are expressed as **tools** (= workflow steps), **skills** (= process docs), and **system_prompt** (= flow definition), then exposed over HTTP by the LangGraph Platform runtime + a thin FastAPI app.

## The load-bearing principle: single Postgres, layered extensions

**If a capability can be provided by a Postgres extension, use the Postgres extension — do not introduce a third service.** The compose stack therefore collapses to **one Postgres service**, no Redis / vector DB / standalone broker. See [postgres-as-platform](../postgres-as-platform/SKILL.md) for the tiered extension model and decision matrix:

- **Tier 1 (dev+prod default):** `pgvector` (RAG/vectors) · `pgai` (in-DB LLM/embedding) · `pgmq` (task queue) · `pg_cron` (scheduled dispatch)
- **Tier 2 (prod/compliance, opt-in):** PgBouncer · PostgreSQL Anonymizer · PGAudit · wal-g
- **Tier 3 (situational, docs only):** pg_search/ParadeDB (hybrid BM25), etc.

## How this skill relates to other layers

This skill owns the **map and the routing rules**. It does not own any concrete mechanism.

- Persistence / queue / vector / scheduling → [postgres-as-platform](../postgres-as-platform/SKILL.md).
- HTTP serving / endpoints / request shapes → [fastapi-serving](../fastapi-serving/SKILL.md).
- Writing a deepagent / tools-as-steps / skills format → [deepagent-authoring](../deepagent-authoring/SKILL.md).
- Scaffolding / testing gates / dev-vs-prod / quality gates → [dev-workflow](../dev-workflow/SKILL.md).

When two layers could plausibly apply, prefer the more specific one. `harness-core` is only the entry point.

## The fixed 3-step recipe for adding a new agent

Mirrors lerdrail's "drop a `SKILL.md` directory" convention. Full template: [references/adding-an-agent.md](references/adding-an-agent.md).

1. **Create the module** `src/<pkg>/agents/<name>/` with:
   - `graph.py` — `build_graph()` returns the compiled graph from `create_deep_agent(model=get_model(), tools=[…], memory=[AGENTS.md], skills=[./skills], backend=FilesystemBackend(...), checkpointer=get_saver(), store=get_store())`.
   - `__init__.py` — exports the compiled `graph`.
   - optional `AGENTS.md` (agent identity → system prompt), `tools.py` (`@tool` functions = workflow steps), `skills/` (on-demand process docs).
2. **Register in `langgraph.json`** — add `"<name>": "./src/<pkg>/agents/<name>/__init__.py:graph"` under `graphs`.
3. **Import in `registry.py`** — `AGENTS["<name>"] = graph`.

→ The agent is now reachable at `POST /runs/stream` (`assistant_id="<name>"`) and listed at `GET /agents`.

## Quick reference

| Want to… | Do |
|---|---|
| Understand the stack at a glance | [references/tech-stack.md](references/tech-stack.md) |
| See the canonical directory layout | [references/project-structure.md](references/project-structure.md) |
| Add a new workflow agent | [references/adding-an-agent.md](references/adding-an-agent.md) |
| Decide where a capability lives | decision tables in [postgres-as-platform](../postgres-as-platform/SKILL.md) |
| Expose an agent over HTTP | [fastapi-serving](../fastapi-serving/SKILL.md) |
| Start a brand-new project from this pack | [dev-workflow](../dev-workflow/SKILL.md) |

## Common mistakes

| Mistake | Fix |
|---|---|
| Reaching for Redis/Celery/a vector DB by default | Check the [postgres-as-platform](../postgres-as-platform/SKILL.md) decision matrix first — pgmq/pgvector/pgai/pg_cron cover most workflow needs in one DB |
| Putting a whole agent's logic in one giant `graph.py` | Split steps into `tools.py` (`@tool` each); keep `graph.py` as wiring. See [deepagent-authoring](../deepagent-authoring/SKILL.md) |
| Hardcoding a provider/model | Always go through `get_model()` → `init_chat_model(config.MODEL)`; swap via `.env` only |
| Forgetting `langgraph.json` **and** `registry.py` | Both must list the agent — `langgraph.json` drives the runtime, `registry.py` drives the FastAPI layer |
| Loading heavy reference files eagerly | SKILL.md stays short; load `references/*.md` only when the task needs them |
