# pgai-in-db-llm

## Table of Contents
1. [What pgai gives you](#what-pgai-gives-you)
2. [Best-effort availability](#best-effort-availability)
3. [Vectorizer — auto-embedding](#vectorizer--auto-embedding)
4. [In-DB LLM calls](#in-db-llm-calls)
5. [Fallback when pgai is absent](#fallback-when-pgai-is-absent)

## What pgai gives you

pgai (Timescale/Tiger Data) lets you call embedding and LLM-completion APIs **from SQL**, and the **Vectorizer** automates syncing text → pgvector embeddings without an external ETL pipeline. For this harness, its main value is removing a Python embedding service.

## Best-effort availability

pgai is **Tier 1 but best-effort**: it is heavier than the others and may not be present on every image. `extensions.sql` wraps it in a `DO $$ … EXCEPTION … $$` block so its absence emits a WARNING, not an error. **Never make a workflow hard-depend on pgai** — always have the Python-`@tool` fallback (below).

## Vectorizer — auto-embedding

Declare once (DDL), pgai keeps a target table's embeddings current:
```sql
SELECT ai.create_vectorizer(
  'kb_documents'::regclass,
  destination => 'embedding',
  embedding => ai.openai_embedding('text-embedding-3-small', 'OPENAI_API_KEY'),
  chunking => ai.semantic_chunker('kb_documents.body', 800, 200)
);
```
After that, `INSERT`/`UPDATE` into `kb_documents` is auto-embedded into the `embedding` column/vectorize shadow table. Query with standard pgvector operators (`<=>`, `<->`).

Set the provider key as a DB-side secret (`OPENAI_API_KEY` via `set_config` / a secrets table) — **not** by passing the app's key into SQL.

## In-DB LLM calls

```sql
SELECT ai.openai_chat_complete(
  'gpt-4o-mini',
  pgvector.format('Classify this feedback: %s', feedback_text)
);
```
Useful for batch transformations/classifications where you want SQL semantics (JOINs, GROUP BY) over the result.

## Fallback when pgai is absent

Embed in the Python tool instead — the agent never needs to know which path is live:
```python
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from <pkg>.platform import get_vectorstore

@tool
def embed_and_store(text: str) -> int:
    """Embed text and store it in the knowledge base; returns stored id count."""
    # get_vectorstore() uses OpenAIEmbeddings under the hood when pgai is absent
    get_vectorstore().add_texts([text])
    return 1
```

Keep the tool interface identical to the pgai path so the agent's prompt doesn't change between environments.
