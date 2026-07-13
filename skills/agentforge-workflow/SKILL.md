---
name: agentforge-workflow
description: Use when doing harness-engineering in an agentforge project — scaffolding from the template, adding/extending an agent, running testing and quality gates, or distinguishing dev vs prod. Orchestrates the lifecycle and defers mechanism to the other four skills.
---

# agentforge-workflow

## Overview

This skill is the **orchestrator** for building with agentforge. It sequences the lifecycle and injects project-specific gates, deferring the *how* to the other skills:

- *What stack, what structure, how to add an agent* → [harness-core](../harness-core/SKILL.md)
- *Where a capability lives* → [postgres-as-platform](../postgres-as-platform/SKILL.md)
- *How agents are served* → [fastapi-serving](../fastapi-serving/SKILL.md)
- *How an agent is written* → [deepagent-authoring](../deepagent-authoring/SKILL.md)

## The lifecycle

```
1. Scaffold      copy template/ → new project; rename <pkg>; uv sync; .env
2. Build agent   3-step recipe (harness-core): module → langgraph.json → registry.py
3. Test gates    run the gates that apply to this module type
4. Run dev       docker compose -f docker-compose.dev.yml up; verify /agents + /runs/stream
5. Run prod      docker compose -f docker-compose.prod.yml up -d; verify
6. Quality gates pre-commit checklist
7. Commit        branch off main; conventional message; one concern per commit
```

Details: [references/scaffolding.md](references/scaffolding.md), [references/dev-vs-prod.md](references/dev-vs-prod.md).

## Testing-gate matrix

Per module type, run these gates (see [references/testing-gates.md](references/testing-gates.md)):

| Module type | Gate(s) |
|---|---|
| Skeleton / config / platform | `uv run pytest` (import + construct) |
| One agent | smoke-invoke its graph with a fake model; assert it produces a message |
| A `@tool` | unit test the function in isolation (no graph needed) |
| FastAPI endpoint | TestClient against `/agents`, `/custom/invoke` |
| `langgraph.json` change | assert it parses + the named graph imports |
| Docker / compose | `docker compose -f <env>.yml config`; then a real `up` health check |

## Quality gates (pre-commit)

Nine-item checklist (see [references/quality-gates.md](references/quality-gates.md)):
1. `uv run pytest` green
2. `uv run ruff check .` clean
3. `uv run ruff format --check .` clean
4. no debugger leftovers (`grep -rn "breakpoint\|pdb.set_trace" src`)
5. `workspace/` not committed (gitignored)
6. `.env` not committed
7. `uv.lock` committed if deps changed
8. new agent registered in **both** `langgraph.json` and `registry.py`
9. reversibility: any DB change has a rollback path

One-shot:
```bash
uv run pytest && uv run ruff check . && uv run ruff format --check . \
  && ! grep -rn "breakpoint\|pdb.set_trace" src \
  && git diff --cached --name-only | grep -qv '\.env$'
```

## Branch & commit discipline

- `main` — hands-off, always green.
- `dev` — integration branch (optional at this scale).
- `feature/<name>` or `agent/<name>` — one per unit of work, off `main`.
- Example agents go on `examples/<name>` branches, never `main`.
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`); one concern per commit.

## Quick reference

| Want to… | Read |
|---|---|
| Start a new project from template/ | [references/scaffolding.md](references/scaffolding.md) |
| Know which tests to run | [references/testing-gates.md](references/testing-gates.md) |
| Understand dev vs prod compose | [references/dev-vs-prod.md](references/dev-vs-prod.md) |
| Pre-commit checklist | [references/quality-gates.md](references/quality-gates.md) |

## Common mistakes

| Mistake | Fix |
|---|---|
| Committing `.env` / `workspace/` | Both gitignored; the quality-gate one-shot catches `.env` |
| Registering an agent in only one place | Both `langgraph.json` and `registry.py` — quality gate #8 |
| Skipping the smoke test for a new agent | Always smoke-invoke with a fake model before declaring done |
| Running prod compose with source mounts / dev deps | prod uses `--frozen --no-dev` and no mounts — see dev-vs-prod |
| Direct DB access bypassing `platform.py` | All DB via the platform handles |
