# testing-gates

## Table of Contents
1. [Run the gates that apply](#run-the-gates-that-apply)
2. [Skeleton tests](#skeleton-tests)
3. [Agent smoke test (fake model)](#agent-smoke-test-fake-model)
4. [Tool unit tests](#tool-unit-tests)
5. [FastAPI endpoint tests](#fastapi-endpoint-tests)

## Run the gates that apply

Not every module needs every test. Match the gate to the module type:

| Module type | Test file | What it asserts |
|---|---|---|
| Skeleton / config / platform | `tests/test_skeleton.py` | app imports; registry shape; `langgraph.json` parses; platform handles construct |
| One agent | `tests/agents/test_<name>.py` | graph builds; smoke-invoke with a fake model produces a final message |
| A `@tool` | `tests/tools/test_<tool>.py` | function correctness in isolation |
| FastAPI endpoint | `tests/test_api.py` | TestClient hits `/agents`, `/custom/invoke` |
| `langgraph.json` change | (part of skeleton test) | JSON valid; named graph path imports |

Run all: `uv run pytest`. Run one: `uv run pytest tests/agents/test_<name>.py`.

## Skeleton tests

Shipped with the template:
```python
def test_app_imports():
    from <pkg>.app.main import app
    assert app is not None

def test_registry_is_dict():
    from <pkg>.registry import AGENTS
    assert isinstance(AGENTS, dict)

def test_langgraph_json_parses():
    import json, pathlib
    cfg = json.loads(pathlib.Path("langgraph.json").read_text())
    assert "graphs" in cfg
```

## Agent smoke test (fake model)

Use `GenericFakeChatModel` so the test needs no API key:
```python
from langchain_core.messages import AIMessage
from langchain_community.chat_models.fake import GenericFakeChatModel

def test_research_agent_smoke(monkeypatch):
    fake = GenericFakeChatModel(messages=iter([AIMessage(content="done.")]))
    monkeypatch.setattr("<pkg>.agents.research_summary.models", "get_model", lambda: fake)
    # or inject at build time
    from <pkg>.agents.research_summary.graph import build_graph
    graph = build_graph()
    # use an in-memory checkpointer to avoid needing PG
    result = graph.invoke({"messages":[{"role":"user","content":"hi"}]})
    assert result["messages"][-1].content
```

## Tool unit tests

Tools are plain functions — test them directly, no graph:
```python
def test_kb_search_returns_list(monkeypatch):
    monkeypatch.setattr("<pkg>.platform", "get_vectorstore", lambda: FakeStore())
    from <pkg>.agents.cs.tools import kb_search
    out = kb_search.invoke({"query":"refund", "k":2})
    assert isinstance(out, list)
```

## FastAPI endpoint tests

```python
from fastapi.testclient import TestClient
from <pkg>.app.main import app

def test_agents_listing():
    r = TestClient(app).get("/agents")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

Use a temporary/in-memory Postgres (or monkeypatch the platform handles) so endpoint tests don't require a live DB.
