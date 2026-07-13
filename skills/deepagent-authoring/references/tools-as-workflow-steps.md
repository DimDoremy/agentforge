# tools-as-workflow-steps

## Table of Contents
1. [The mental model](#the-mental-model)
2. [Anatomy of a good tool](#anatomy-of-a-good-tool)
3. [Patterns by workflow class](#patterns-by-workflow-class)
4. [Error handling](#error-handling)

## The mental model

In a DeepAgents workflow, **each `@tool` is one workflow step**. The model (via the planning/todo middleware) decides which step to call, in what order, branching on results. Your job is to make each step a crisp, well-named, well-documented capability — not to script the ordering yourself.

Contrast with raw LangGraph: there you'd write nodes and conditional edges by hand. Here, the "routing" is the model reading tool docstrings and prior results. Reserve raw nodes for deterministic gateways the model shouldn't control.

## Anatomy of a good tool

```python
from langchain_core.tools import tool

@tool
def kb_search(query: str, k: int = 4) -> list[dict]:
    """Search the customer-service knowledge base for passages matching the query.

    Use when the customer asks a factual/product/policy question and you need
    authoritative sources before answering. Returns the top-k passages with
    scores and metadata. Prefer this over answering from memory.

    Args:
        query: A natural-language or keyword query.
        k: Number of passages to return (default 4).
    """
    from <pkg>.platform import get_vectorstore
    docs = get_vectorstore().similarity_search_with_score(query, k=k)
    return [{"content": d.page_content, "score": s, "metadata": d.metadata} for d, s in docs]
```

Checklist:
- **Name** = verb + object (`kb_search`, `enqueue_publish`, `classify_intent`).
- **Docstring** = the tool's contract with the model: what it does, **when to use it**, what it returns. This is the single most important field.
- **Typed args** — the schema is derived from type hints; no `Any`.
- **Returns plain JSON-able data** — dicts/lists/strings, not ORM objects.
- **No side effects hidden** — if it writes (queue, file, DB), say so in the docstring.

## Patterns by workflow class

### AI customer service (routing/branching)
- `classify_intent(message) -> str` — intent routing step.
- `kb_search(query) -> list[dict]` — RAG retrieval (pgvector).
- `draft_reply(context) -> str` — generation step.
- `escalate_to_human(reason) -> str` — handoff step.

### Customer research (pipeline)
- `generate_questions(topic) -> list[str]`
- `store_responses(responses) -> int` (pgmq or table)
- `analyze_responses(responses) -> dict` (LLM, possibly pgai)
- `write_report(outline) -> str` (FilesystemBackend)

### Multi-platform publish (fan-out)
- `draft(content) -> str`
- `adapt_for_platform(content, platform) -> str`
- `enqueue_publish(platform, content, run_at) -> str` — writes pgmq (+ pg_cron row)
- `list_scheduled() -> list[dict]`

## Error handling

Let tools **return** error information the model can act on, rather than raising across the agent boundary:

```python
@tool
def fetch_url(url: str) -> dict:
    """Fetch a URL. Returns {'ok': True, 'text': ...} or {'ok': False, 'error': ...}."""
    import httpx
    try:
        return {"ok": True, "text": httpx.get(url, timeout=20.0).text}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

The model can then retry, try a different URL, or report failure — much more useful than a crashed run. Reserve exceptions for truly unrecoverable internal bugs.
