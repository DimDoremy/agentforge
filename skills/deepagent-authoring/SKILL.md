---
name: deepagent-authoring
description: Use when writing or modifying a workflow-level agent in an agentforge project — constructing the agent with create_deep_agent, defining @tool functions that represent workflow steps, authoring the agent's AGENTS.md (identity/system prompt) and on-demand skills (SKILL.md), or configuring subagents. Owns the "every agent is a create_deep_agent instance" convention and the tools-as-workflow-steps pattern. Delegates where the tools' data lives to postgres-as-platform, and how the agent is exposed to fastapi-serving.
---

# deepagent-authoring

## Overview

Every agent in this harness is **one `create_deep_agent(...)` instance** — that compiled graph is what gets registered in `langgraph.json` and served. DeepAgents gives you, for free:

- **planning/todo** — the agent breaks a task into steps itself;
- **skills middleware** — loads `skills/*/SKILL.md` on demand (same format as lerdrail);
- **memory** — `AGENTS.md` is always part of the system prompt;
- **subagents** — delegate sub-tasks;
- **FilesystemBackend** — scratch files under `workspace/`.

A **workflow** (customer service, research, multi-platform publish) is expressed by choosing the agent's **tools** (each tool = one workflow step), its **AGENTS.md** (the flow definition + rules), and its **skills/** (detailed process docs). You rarely write raw LangGraph node/edge code.

## The authoring triad

| Artifact | File | Role |
|---|---|---|
| Identity / flow definition | `AGENTS.md` | Always in system prompt: who the agent is, the workflow steps, the rules |
| Workflow steps | `tools.py` (`@tool` each) | The concrete actions the agent can take (search KB, enqueue publish, fetch URL, …) |
| Detailed process docs | `skills/<subflow>/SKILL.md` | Loaded on demand when a step needs a deep procedure |

## Canonical construction

```python
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from <pkg>.models import get_model
from <pkg>.platform import get_saver, get_store

_HERE = Path(__file__).parent

def build_graph():
    return create_deep_agent(
        model=get_model(),
        tools=[...],                            # from tools.py — the workflow steps
        memory=[str(_HERE / "AGENTS.md")],
        skills=[str(_HERE / "skills")],
        backend=FilesystemBackend(root_dir=str(_HERE / "workspace")),
        checkpointer=get_saver(),
        store=get_store(),
    )

graph = build_graph()
```

Full template + 3-step registration: [harness-core/references/adding-an-agent.md](../../harness-core/references/adding-an-agent.md).

## How this skill relates to other layers

- **Where tool data lives** (Postgres, pgvector, pgmq, pg_cron, pgai) → [postgres-as-platform](../postgres-as-platform/SKILL.md).
- **How the built agent is reached over HTTP** → [fastapi-serving](../fastapi-serving/SKILL.md).
- **The 3-step add-an-agent recipe** → [harness-core](../harness-core/SKILL.md).

## Quick reference

| Want to… | Read |
|---|---|
| Design tools as workflow steps | [references/tools-as-workflow-steps.md](references/tools-as-workflow-steps.md) |
| Write the AGENTS.md + on-demand skills | [references/skills-format.md](references/skills-format.md) |
| Delegate sub-tasks to subagents | [references/subagents.md](references/subagents.md) |

## Common mistakes

| Mistake | Fix |
|---|---|
| Writing raw LangGraph nodes for a workflow | Use tools + AGENTS.md; reach for raw nodes only for hard routing the model can't express |
| God-tool (one `@tool` that does everything) | One responsibility per tool; the model composes them |
| Vague `@tool` docstrings | The docstring **is** the tool's description to the model — be precise about when/how to use it |
| Heavy `AGENTS.md` | Keep identity + flow overview there; push deep procedures into `skills/*/SKILL.md` (loaded on demand) |
| Hardcoding the model | Always `get_model()`; swap via `.env` |
| Reaching into Postgres bypassing `platform.py` | All DB access via the platform handles — singletons, correct DSN |
