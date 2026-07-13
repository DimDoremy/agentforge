"""Agent registry — the FastAPI layer's source of truth for "which agents exist".

Each agent module exports a compiled ``graph`` (see
``skills/harness-core/references/adding-an-agent.md``). Import it here and add
it to :data:`AGENTS`. The same key must also appear under ``graphs`` in
``langgraph.json`` (the runtime's source of truth) — gate #8 in the quality
checks.

The skeleton ships empty. After adding the first agent::

    from .agents.research_summary import graph as research_summary_graph
    AGENTS["research_summary"] = research_summary_graph
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentInfo:
    """Public metadata for one registered agent."""

    id: str
    description: str = ""


# id -> compiled graph. Starts empty; fill as agents are added.
AGENTS: dict[str, Any] = {}


def list_agents() -> list[AgentInfo]:
    """Return agent metadata for the ``GET /agents`` discovery endpoint."""
    info: list[AgentInfo] = []
    for agent_id, graph in AGENTS.items():
        description = ""
        for prop in ("description", "name"):
            val = getattr(graph, prop, None)
            if isinstance(val, str):
                description = val
                break
        info.append(AgentInfo(id=agent_id, description=description))
    return info
