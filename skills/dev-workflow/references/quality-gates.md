# quality-gates

## Table of Contents
1. [Pre-commit checklist](#pre-commit-checklist)
2. [One-shot command](#one-shot-command)
3. [Reversibility rule](#reversibility-rule)

## Pre-commit checklist

Run all nine before committing. Each catches a real failure mode.

| # | Gate | Command / check |
|---|---|---|
| 1 | Tests green | `uv run pytest` |
| 2 | Lint clean | `uv run ruff check .` |
| 3 | Format clean | `uv run ruff format --check .` |
| 4 | No debugger leftovers | `! grep -rn "breakpoint\|pdb.set_trace" src` |
| 5 | `workspace/` not staged | not in `git diff --cached --name-only` |
| 6 | `.env` not staged | not in `git diff --cached --name-only` |
| 7 | `uv.lock` staged if deps changed | if `pyproject.toml` changed, `uv.lock` changed too |
| 8 | New agent registered in both | present in `langgraph.json` `graphs` **and** `registry.AGENTS` |
| 9 | Reversibility | any DB/migration change has a documented rollback |

## One-shot command

```bash
uv run pytest \
  && uv run ruff check . \
  && uv run ruff format --check . \
  && ! grep -rn "breakpoint\|pdb.set_trace" src \
  && ! git diff --cached --name-only | grep -Eq '(^|/)\.env$' \
  && ! git diff --cached --name-only | grep -Eq 'workspace/.+' \
  && echo "ALL GATES GREEN"
```

## Reversibility rule

Every change to the DB shape (a new extension, a new `ensure_queue`, a `PostgresStore`/`PGVector` collection) must be rollback-able:

- Extensions: `CREATE EXTENSION IF NOT EXISTS` is paired with the ability to `DROP EXTENSION` (document it; never auto-drop in code).
- Queues: `pgmq` queues can be archived/dropped; `entrypoint`/`setup_all` is idempotent so re-run after rollback is safe.
- Vector collections: `PGVector` collections are named and droppable.

If a change isn't reversible (e.g. a destructive data migration), call it out explicitly in the commit message and the PR.
