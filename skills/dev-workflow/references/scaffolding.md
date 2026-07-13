# scaffolding

## Table of Contents
1. [Start from template/](#start-from-template)
2. [Rename the package](#rename-the-package)
3. [First-run checks](#first-run-checks)

## Start from template/

`template/` is the runnable skeleton. To start a new project:

```bash
cp -r agentforge/template /path/to/new-project
cd /path/to/new-project
git init
```

## Rename the package

The skeleton's import package is `agentforge_template` (a placeholder). Rename it to the project slug:

```bash
PKG=myproject
git mv src/agentforge_template src/$PKG
grep -rl agentforge_template . --include='*.py' --include='*.toml' --include='*.json' \
  | xargs sed -i "s/agentforge_template/$PKG/g"
```

Then edit:
- `pyproject.toml` — `name`, `version`, `description`, the `[project.scripts]` entry, `[tool.hatch]`/build config package path.
- `langgraph.json` — the `graphs` paths (when you add agents).
- `README.md` — replace the template prose.

## First-run checks

```bash
cp .env.example .env       # fill MODEL, provider key, DB creds
uv sync                    # creates .venv from pyproject + uv.lock
uv run pytest              # skeleton tests green
```

Then bring up dev:
```bash
docker compose -f docker-compose.dev.yml up
# in another terminal:
curl localhost:8000/agents   # -> []
```

At this point the harness is empty (no agents) but fully wired. Add the first agent via the [3-step recipe](../../harness-core/references/adding-an-agent.md).
