# Import guide — using agentforge as a skill pack

agentforge's `skills/` directory is a lerdrail-style skill pack. You can import
it into another project so an agent (ZCode, Claude Code, …) follows these
conventions when doing harness engineering there.

## Option 1 — link into a per-user skills directory

```bash
# ZCode example (adjust the target for your agent host)
ln -s /path/to/agentforge/skills/harness-core        ~/.zcode/skills/harness-core
ln -s /path/to/agentforge/skills/postgres-as-platform ~/.zcode/skills/postgres-as-platform
ln -s /path/to/agentforge/skills/fastapi-serving     ~/.zcode/skills/fastapi-serving
ln -s /path/to/agentforge/skills/deepagent-authoring ~/.zcode/skills/deepagent-authoring
ln -s /path/to/agentforge/skills/harness-workflow        ~/.zcode/skills/harness-workflow
```

Each `SKILL.md`'s `description` ("Use when…") becomes a routing trigger; the host
agent loads it when a task matches, and pulls `references/*.md` on demand.

## Option 2 — copy `skills/` into the target project

```bash
cp -r /path/to/agentforge/skills /path/to/target-project/.agentforge-skills
```
Then point the host agent at that directory. This bakes the conventions into the
repo (good for team consistency) at the cost of updates needing a re-copy.

## Option 3 — global preconfiguration

Place the skills in a shared location and reference them from the host agent's
global config so **every** new project gets them automatically. This is the
"预先全局配置" mode: configure once, every project inherits.

## After importing

In the target project, the agent will:
1. Match `harness-workflow` at the start of harness work → scaffold from `template/`.
2. Follow the 3-step recipe (`harness-core`) to add agents.
3. Route persistence/queue/vector decisions through `postgres-as-platform`.
4. Expose agents via `fastapi-serving`; write them per `deepagent-authoring`.

The skills are read-only conventions — they never execute code themselves.
