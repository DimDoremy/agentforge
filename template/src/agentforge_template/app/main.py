"""FastAPI app — exposes registered agents over HTTP.

Two surfaces (see ``skills/fastapi-serving/SKILL.md``):

1. The **LangGraph Platform runtime**, mounted via ``add_routes``. Owns
   ``/threads``, ``/runs/stream``, ``/runs``, ``/assistants`` — the primary way
   frontends reach an agent (with streaming for free).
2. **Custom convenience endpoints** — ``GET /agents`` (discovery) and
   ``POST /custom/invoke`` (one-shot JSON, no streaming).

The app is intentionally thin: it does not reimplement the runtime.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .. import registry
from ..config import get_settings


def create_app() -> FastAPI:
    """Build the FastAPI app. Used by the server and by tests (TestClient)."""
    settings = get_settings()
    app = FastAPI(
        title="agentforge",
        description="Workflow-level AI agent harness — FastAPI + LangGraph + DeepAgents.",
        version="0.1.0",
    )

    # (1) Mount the full LangGraph runtime. The import path varies across
    # langgraph-cli versions; try the free-function form first, then the
    # runtime method form. If neither is available in dev, log and continue —
    # the custom endpoints still work, and the real container provides it.
    _mount_runtime(app)

    # (2) Custom convenience endpoints.
    @app.get("/agents")
    def list_agents() -> list[dict[str, Any]]:
        """List registered agents (discovery for UI pickers)."""
        return [a.__dict__ for a in registry.list_agents()]

    @app.post("/custom/invoke")
    def custom_invoke(payload: InvokeRequest) -> InvokeResponse:
        """One-shot JSON invocation: message in, final AI message out."""
        graph = registry.AGENTS.get(payload.assistant_id)
        if graph is None:
            raise HTTPException(
                status_code=404,
                detail=f"unknown assistant_id {payload.assistant_id!r}; "
                f"known: {sorted(registry.AGENTS)}",
            )
        thread_id = payload.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(
            {"messages": [{"role": "user", "content": payload.message}]},
            config=config,
        )
        final = ""
        messages = result.get("messages") if isinstance(result, dict) else None
        if messages:
            last = messages[-1]
            final = getattr(last, "content", str(last))
        return InvokeResponse(thread_id=thread_id, message=final)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _mount_runtime(app: FastAPI) -> None:
    """Best-effort mount of the LangGraph Platform runtime onto ``app``."""
    import logging

    log = logging.getLogger(__name__)
    try:
        # Preferred: free-function add_routes (langgraph-platform / langgraph-cli).
        from langgraph.runtime import add_routes  # type: ignore

        add_routes(app)  # type: ignore[arg-type]
        log.info("LangGraph runtime mounted via langgraph.runtime.add_routes")
        return
    except Exception:  # noqa: BLE001
        pass
    try:
        from langgraph.runtime import get_runtime  # type: ignore

        get_runtime().add_routes(app)  # type: ignore[attr-defined]
        log.info("LangGraph runtime mounted via get_runtime().add_routes")
        return
    except Exception:  # noqa: BLE001
        pass
    log.warning(
        "LangGraph runtime helpers unavailable in this environment — "
        "only /agents and /custom/invoke are mounted. The runtime is provided "
        "by the container (`langgraph dev`/`up`), not this app process."
    )


# --- request / response models ----------------------------------------------


class InvokeRequest(BaseModel):
    assistant_id: str
    message: str
    thread_id: str | None = None


class InvokeResponse(BaseModel):
    thread_id: str
    message: str


# Module-level app for ``uvicorn <pkg>.app.main:app``.
app = create_app()
