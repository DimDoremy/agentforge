"""LLM model access — the single point where a chat model is constructed.

Provider-agnostic by design: :func:`get_model` delegates to LangChain's
``init_chat_model`` with the ``MODEL`` string from env (e.g. ``openai:gpt-4o-mini``
or ``anthropic:claude-3-5-sonnet-latest``). Swap providers via ``.env`` only;
no code changes, no per-agent model wiring.
"""

from __future__ import annotations

from functools import lru_cache

from langchain.chat_models import init_chat_model

from .config import get_settings


@lru_cache
def get_model():
    """Return a cached chat model selected by the ``MODEL`` env string.

    Examples of valid ``MODEL`` values (LangChain ``init_chat_model`` syntax):
        - ``openai:gpt-4o-mini``
        - ``anthropic:claude-3-5-sonnet-latest``
        - ``google_genai:gemini-1.5-flash``
    """
    settings = get_settings()
    return init_chat_model(model=settings.model)
