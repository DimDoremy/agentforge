# skills-format

## Table of Contents
1. [AGENTS.md vs SKILL.md](#agentsmd-vs-skillmd)
2. [AGENTS.md](#agentsmd)
3. [SKILL.md (on-demand skills)](#skillmd-on-demand-skills)

## AGENTS.md vs SKILL.md

DeepAgents loads **two kinds** of markdown, at different times:

| File | When loaded | Scope | Use for |
|---|---|---|---|
| `AGENTS.md` | **Always** — folded into the system prompt on every run | One agent's identity + top-level flow + invariants | "You are the Acme support agent. Steps: classify → retrieve → draft → (maybe) escalate. Never invent policy." |
| `skills/<subflow>/SKILL.md` | **On demand** — the agent reads it when it decides the subflow applies | A specific, deeper procedure | "How to handle a refund request" — loaded only when relevant |

Keep `AGENTS.md` short (it's paid for on every turn). Push depth into skills.

## AGENTS.md

```markdown
# <Agent Name>

You are the <role> for <scope>.

## Your workflow
1. <step one>
2. <step two>
3. ...

## Tools available
- `kb_search` — retrieve from the knowledge base
- `enqueue_publish` — queue a post for publishing
- ...

## Rules
- Never invent policy; always ground answers in `kb_search` results.
- Escalate to a human when confidence < threshold.
- ...
```

Wire it via `memory=[str(_HERE / "AGENTS.md")]` in `create_deep_agent`.

## SKILL.md (on-demand skills)

Same format as lerdrail (and as this very pack). Front-matter + body:

```markdown
---
name: handle-refund
description: Use when the customer requests a refund or cancellation of an order. ...
---

# handle-refund

## Overview
...

## Steps
1. Verify order via `lookup_order`.
2. Check eligibility per policy doc.
3. ...

## Common mistakes
| Mistake | Fix |
|---|---|
| ... | ... |
```

Directory layout:
```
<agent>/
└── skills/
    └── <subflow>/
        ├── SKILL.md          (required)
        └── references/       (optional — loaded on demand)
```

Wire via `skills=[str(_HERE / "skills")]` in `create_deep_agent`. The middleware matches a skill's `description` against the current task and loads it when relevant.

**Reuse opportunity:** this *pack's* `skills/` (harness-core, postgres-as-platform, …) follow the exact same format — consistency across the harness layer and the product agent layer.
