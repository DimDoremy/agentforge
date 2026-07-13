# agentforge template

Runnable skeleton for the [agentforge](../README.md) harness pack. Copy this
directory to start a new workflow-level agent project.

## Status

Wired and runnable, **shipped with no agents**. The harness is empty by design —
add the first agent via the 3-step recipe in
[`../skills/harness-core/references/adding-an-agent.md`](../skills/harness-core/references/adding-an-agent.md).

## Quick start

```bash
cp .env.example .env        # fill MODEL + provider key + DB creds
uv sync                     # local venv (optional; docker also works)

# Docker route (recommended — single Postgres + agent):
docker compose -f docker-compose.dev.yml up
# another terminal:
curl localhost:8000/agents   # -> []   (empty registry, as expected)
```

## What's here

| Path | Role |
|---|---|
| `pyproject.toml` | uv deps + tool config |
| `langgraph.json` | runtime config; `graphs` starts empty `{}` |
| `Dockerfile` | multi-stage dev/prod agent image |
| `docker/postgres.Dockerfile` | Postgres + Tier-1 extensions |
| `docker/extensions.sql` | `CREATE EXTENSION` (idempotent, tiered failure handling) |
| `docker/entrypoint.sh` | wait-for-pg → extensions → `setup_all()` → runtime |
| `docker-compose.dev.yml` / `.prod.yml` | two standalone envs |
| `src/agentforge_template/` | the package (rename on scaffold) |
| `config.py` | `Settings` — single env source |
| `platform.py` | Postgres platform: saver/store/pgmq/vectorstore/cron |
| `models.py` | `get_model()` — pluggable via `MODEL` env |
| `registry.py` | `AGENTS` dict + `list_agents()` |
| `app/main.py` | FastAPI app: `add_routes` + `/agents` + `/custom/invoke` |
| `agents/` | one directory per agent (empty) |
| `tests/` | skeleton + agent tests |

## Rename for a new project

See [`../skills/harness-workflow/references/scaffolding.md`](../skills/harness-workflow/references/scaffolding.md).
