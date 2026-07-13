"""Skeleton tests — verify the harness wiring with NO live Postgres / NO LLM key.

These run in any environment (CI, fresh clone). They assert:
  * the package imports;
  * the FastAPI app constructs and exposes the custom endpoints;
  * the registry shape is correct (starts empty);
  * langgraph.json parses and has the expected keys.

Anything needing a live DB or an LLM provider lives in agent-specific tests.
"""

from __future__ import annotations

import json
from pathlib import Path


def test_package_imports():
    import agentforge_template

    assert agentforge_template.__version__


def test_settings_constructs():
    from agentforge_template.config import get_settings

    s = get_settings()
    assert s.model
    assert s.db_dsn.startswith("postgresql://")
    assert s.db_name


def test_registry_is_empty_dict():
    # fresh skeleton has no agents
    from agentforge_template import registry

    assert isinstance(registry.AGENTS, dict)
    assert registry.AGENTS == {}
    assert registry.list_agents() == []


def test_app_constructs_and_has_custom_routes():
    from fastapi.testclient import TestClient

    from agentforge_template.app.main import create_app

    client = TestClient(create_app())
    r = client.get("/agents")
    assert r.status_code == 200
    assert r.json() == []

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_custom_invoke_rejects_unknown_assistant():
    from fastapi.testclient import TestClient

    from agentforge_template.app.main import create_app

    client = TestClient(create_app())
    r = client.post(
        "/custom/invoke",
        json={"assistant_id": "does_not_exist", "message": "hi"},
    )
    assert r.status_code == 404


def test_langgraph_json_parses():
    cfg = json.loads(Path("langgraph.json").read_text())
    assert "dependencies" in cfg
    assert "graphs" in cfg
    assert isinstance(cfg["graphs"], dict)
    # skeleton: no graphs registered yet
    assert cfg["graphs"] == {}
    assert cfg["env"] == ".env"
