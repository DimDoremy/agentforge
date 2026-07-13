# pgvector-rag

## Table of Contents
1. [When to use](#when-to-use)
2. [Prerequisites](#prerequisites)
3. [The vectorstore handle](#the-vectorstore-handle)
4. [A RAG tool pattern](#a-rag-tool-pattern)
5. [Indexing](#indexing)

## When to use

A workflow needs **semantic retrieval** — customer-service knowledge base lookup, research-source recall. pgvector stores embeddings next to relational data and serves similarity search. Reach for it instead of an external vector DB unless you have a proven scale need (then see Tier 3).

## Prerequisites

- `vector` extension present (Tier 1, hard guarantee — base image ships it).
- An embedding model. Prefer `pgai` Vectorizer to auto-embed (see [pgai-in-db-llm.md](pgai-in-db-llm.md)); if pgai is unavailable, embed in the Python tool with a LangChain embeddings model.
- `langchain-postgres` provides the `PGVector` vectorstore.

## The vectorstore handle

In `platform.py`:
```python
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings   # or your provider
from .config import settings

_vectorstore: PGVector | None = None


def get_vectorstore() -> PGVector:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = PGVector(
            connection=settings.DB_DSN,
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="kb",
            pre_collection_config=...,   # optional: HNSW index params
            use_jsonb=True,
        )
    return _vectorstore
```

`PGVector` creates its table/collection lazily; no extra `setup()` needed.

## A RAG tool pattern

Each workflow step is a `@tool`; retrieval is just another step the agent can call:
```python
from langchain_core.tools import tool
from <pkg>.platform import get_vectorstore

@tool
def kb_search(query: str, k: int = 4) -> list[dict]:
    """Search the knowledge base for passages relevant to the query."""
    docs = get_vectorstore().similarity_search_with_score(query, k=k)
    return [{"content": d.page_content, "score": s, "metadata": d.metadata} for d, s in docs]
```

Ingestion (separate from the agent) writes documents:
```python
get_vectorstore().add_documents(docs, ids=[...])
```

## Indexing

- Default ANN index works for moderate sizes.
- For >100k vectors, set HNSW params via `pre_collection_config` (m, ef_construction).
- For hybrid keyword+vector search, escalate to **Tier 3 pg_search/ParadeDB** — see [extension-tiers.md](extension-tiers.md).
- Keep embedding dimension consistent per collection — switching models means re-embedding.
