# Adding a workflow agent

> The detailed 3-step recipe lives in
> [`skills/harness-core/references/adding-an-agent.md`](../skills/harness-core/references/adding-an-agent.md).
> This page is the short version with the reasoning.

## The 3 steps

1. **Create the module** `src/<pkg>/agents/<name>/`:
   - `graph.py` — `build_graph()` → `create_deep_agent(...)`.
   - `__init__.py` — exports the compiled `graph`.
   - optional `tools.py` (`@tool` each = one workflow step), `AGENTS.md`
     (identity/system prompt), `skills/` (on-demand process docs), `workspace/`.
2. **Register in `langgraph.json`** — add `"<name>": "./src/<pkg>/agents/<name>/__init__.py:graph"`.
3. **Import in `registry.py`** — `AGENTS["<name>"] = graph`.

→ Reachable at `POST /runs/stream` (`assistant_id="<name>"`) and listed at `GET /agents`.

## Minimal `graph.py`

```python
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from <pkg>.models import get_model
from <pkg>.platform import get_saver, get_store
from <pkg>.agents.<name>.tools import step_one, step_two   # your @tool steps

_HERE = Path(__file__).parent

def build_graph():
    return create_deep_agent(
        model=get_model(),
        tools=[step_one, step_two],
        memory=[str(_HERE / "AGENTS.md")],
        skills=[str(_HERE / "skills")],
        backend=FilesystemBackend(root_dir=str(_HERE / "workspace")),
        checkpointer=get_saver(),
        store=get_store(),
    )

graph = build_graph()
```

## Designing the workflow

- **Tools = steps.** Each `@tool` is one workflow step (search KB, enqueue publish,
  classify intent, …). The model composes them. See
  [`skills/deepagent-authoring/references/tools-as-workflow-steps.md`](../skills/deepagent-authoring/references/tools-as-workflow-steps.md).
- **AGENTS.md = flow definition.** Identity + the ordered steps + the rules; kept
  short (paid on every turn).
- **skills/ = deep procedures.** Loaded on demand; same SKILL.md format as this pack.
- **Where tool data lives** → [`postgres-platform.md`](postgres-platform.md).

## Smoke test

Add `tests/agents/test_<name>.py` with a fake model
(`GenericFakeChatModel`) so it runs without an API key — see
[`skills/dev-workflow/references/testing-gates.md`](../skills/dev-workflow/references/testing-gates.md).

## Examples

`main` ships no example agents by design. Concrete workflow examples
(customer service, customer research, multi-platform publishing) live on
`examples/<name>` branches as reference implementations of this recipe.
