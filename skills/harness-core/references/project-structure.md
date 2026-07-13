# project-structure

## Table of Contents
1. [Canonical layout](#canonical-layout)
2. [The two layers](#the-two-layers)
3. [Inside one agent module](#inside-one-agent-module)
4. [Conventions](#conventions)

## Canonical layout

A new project scaffolded from this pack looks like `template/`:

```
<project>/
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml                 # uv: deps + tool config
├── uv.lock                        # committed
├── langgraph.json                 # { dependencies:["."], graphs:{…}, env:".env" }
├── Dockerfile                     # agent image, multi-stage dev/prod
├── docker/
│   ├── postgres.Dockerfile        # FROM pgvector/pgvector:pg16 + Tier-1 extensions
│   ├── extensions.sql             # CREATE EXTENSION (idempotent, tiered failure handling)
│   └── entrypoint.sh              # wait-for-pg → extensions.sql → setup_all → langgraph dev/up
├── docker-compose.dev.yml         # standalone: postgres + agent (reload, source mount)
├── docker-compose.prod.yml        # standalone: postgres + agent (built image, restart)
├── .env.example
├── .dockerignore
└── src/<pkg>/
    ├── __init__.py
    ├── config.py                  # Settings(BaseSettings) — single env source
    ├── platform.py                # PG platform: get_saver/get_store/get_pgmq/get_vectorstore/get_cron
    ├── models.py                  # get_model() = init_chat_model(config.MODEL)
    ├── registry.py                # AGENTS: dict[str, CompiledGraph] + list_agents()
    ├── app/
    │   ├── __init__.py
    │   └── main.py                # FastAPI factory + add_routes + /agents + /custom/invoke
    └── agents/
        └── <name>/                # one directory per agent (see below)
```

## The two layers

- **`skills/`** — the lerdrail-style pack (this file and siblings). Project-agnostic conventions. Travels with the project but is not imported by code; it is read by the agent/developer.
- **`template/` → becomes the project root** — the runnable code. Copy `template/` to start a new project, rename `<pkg>`, and fill `agents/`.

## Inside one agent module

`src/<pkg>/agents/<name>/`:

```
<name>/
├── __init__.py        # exports `graph = build_graph()`
├── graph.py           # create_deep_agent(...) wiring
├── tools.py           # @tool functions — each is one workflow step
├── AGENTS.md          # agent identity + rules → always in system prompt (DeepAgents memory)
├── skills/            # on-demand process docs (same SKILL.md format as lerdrail)
│   └── <subflow>/SKILL.md
└── workspace/         # FilesystemBackend root for file outputs (gitignored)
```

Only `graph.py` + `__init__.py` are mandatory. `tools.py` / `AGENTS.md` / `skills/` / `workspace/` appear when the workflow needs them.

## Conventions

- **Package name `<pkg>`** — rename `agentforge_template` to the project slug on scaffolding.
- **One agent = one directory** — never put two agents' code in the same module.
- **`workspace/` is gitignored** except `.gitkeep` — it is runtime scratch, not source.
- **Config never hardcodes** — all env via `config.Settings`; all model strings via `models.get_model()`.
- **Tests mirror the package** — `tests/agents/test_<name>.py` for each agent.
