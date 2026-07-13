# adding-an-agent

## Table of Contents
1. [The 3-step recipe](#the-3-step-recipe)
2. [Copy-paste template](#copy-paste-template)
3. [Wiring checklist](#wiring-checklist)
4. [Smoke test](#smoke-test)

## The 3-step recipe

1. **Create the module** `src/<pkg>/agents/<name>/`:
   - `graph.py` — `build_graph()` → `create_deep_agent(...)`.
   - `__init__.py` — `from .graph import build_graph` then `graph = build_graph()`.
   - optional `tools.py`, `AGENTS.md`, `skills/`, `workspace/`.
2. **Register in `langgraph.json`** — add `"<name>": "./src/<pkg>/agents/<name>/__init__.py:graph"` to `graphs`.
3. **Import in `registry.py`** — `from .agents.<name> import graph as <name>_graph` and `AGENTS["<name>"] = <name>_graph`.

→ Reachable at `POST /runs/stream` (`assistant_id="<name>"`) and listed at `GET /agents`.

## Copy-paste template

`src/<pkg>/agents/<name>/graph.py`:
```python
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from <pkg>.models import get_model
from <pkg>.platform import get_saver, get_store
from <pkg>.agents.<name>.tools import fetch_url, save_outline  # your @tool steps

_HERE = Path(__file__).parent


def build_graph():
    return create_deep_agent(
        model=get_model(),
        tools=[fetch_url, save_outline],
        memory=[str(_HERE / "AGENTS.md")],
        skills=[str(_HERE / "skills")],
        backend=FilesystemBackend(root_dir=str(_HERE / "workspace")),
        checkpointer=get_saver(),   # PostgresSaver
        store=get_store(),          # PostgresStore (long-term memory; optional)
    )


graph = build_graph()
```

`src/<pkg>/agents/<name>/__init__.py`:
```python
from <pkg>.agents.<name>.graph import graph

__all__ = ["graph"]
```

`src/<pkg>/agents/<name>/tools.py` (each `@tool` is one workflow step):
```python
from langchain_core.tools import tool


@tool
def fetch_url(url: str) -> str:
    """Fetch a URL and return its text. Use for retrieving a source page."""
    import httpx
    return httpx.get(url, timeout=20.0).text


@tool
def save_outline(path: str, content: str) -> str:
    """Write an outline document under this agent's workspace."""
    ...  # write under workspace/, return the saved path
```

`langgraph.json` (add the key):
```json
{
  "dependencies": ["."],
  "graphs": {
    "<name>": "./src/<pkg>/agents/<name>/__init__.py:graph"
  },
  "env": ".env"
}
```

`src/<pkg>/registry.py` (import it):
```python
from <pkg>.agents.<name> import graph as <name>_graph
from <pkg>.agents.<name>.graph import AGENTS_MD_PATH  # if you expose metadata

AGENTS: dict[str, object] = {
    "<name>": <name>_graph,
}
```

## Wiring checklist

- [ ] `graph.py` builds and `import graph` works in isolation.
- [ ] `langgraph.json` `graphs` has the key with the correct dotted path.
- [ ] `registry.py` imports it (so FastAPI's `/agents` lists it).
- [ ] `AGENTS.md` present if the agent needs a fixed identity/system prompt.
- [ ] `workspace/` exists (or the FilesystemBackend creates it) and is gitignored.
- [ ] `tests/agents/test_<name>.py` smoke-invokes the graph with a fake model.

## Smoke test

```bash
uv run langgraph dev
# in another terminal:
curl -X POST localhost:8000/runs/stream \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"<name>","input":{"messages":[{"role":"user","content":"hello"}]},"stream_mode":"messages"}'
curl localhost:8000/agents        # lists "<name>"
```
