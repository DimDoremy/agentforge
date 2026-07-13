# subagents

## Table of Contents
1. [When to use subagents](#when-to-use-subagents)
2. [Defining subagents](#defining-subagents)
3. [A coordinated example](#a-coordinated-example)

## When to use subagents

DeepAgents can spawn **subagents** for sub-tasks. Use them when one workflow genuinely decomposes into independent, self-contained pieces that each warrant their own identity/tools — e.g. "research" and "write" as separate subagents of a report pipeline.

**Don't** use subagents as the default. Most workflow-level agents are better expressed as one agent + several `@tool`s (see [tools-as-workflow-steps.md](tools-as-workflow-steps.md)). Reach for subagents only when:
- A sub-task has a distinct role/identity and its own toolset, **and**
- You want isolation (separate context windows, separate todo plans), **and**
- The overhead is justified (subagents add latency + tokens).

## Defining subagents

Two ways; both produce a `task` tool the parent agent calls to delegate.

### From YAML (`subagents.yaml`)
```yaml
- name: researcher
  description: Researches a topic and returns findings.
  system_prompt: You are a meticulous researcher ...
  model: ${MODEL}            # or a specific model
  tools: [fetch_url, kb_search]
```
Load and pass in:
```python
from deepagents import create_deep_agent, load_subagents

agent = create_deep_agent(
    model=get_model(),
    tools=[...],
    system_prompt=open("AGENTS.md").read(),
    subagents=load_subagents(str(_HERE / "subagents.yaml")),
)
```

### Inline
```python
from deepagents import create_sub_agent

researcher = create_sub_agent({
    "name": "researcher",
    "description": "Researches a topic and returns findings.",
    "system_prompt": "You are a meticulous researcher ...",
    "model": get_model(),
    "tools": [fetch_url, kb_search],
})

agent = create_deep_agent(
    model=get_model(),
    tools=[...],
    subagents=[researcher],
)
```

Custom state fields on the parent propagate to subagents as accessible channels (define a `DeepAgentState` subclass).

## A coordinated example

A research agent delegates to parallel researchers:
```python
agent = create_deep_agent(
    model=get_model(),
    tools=[write_report],
    system_prompt="You coordinate research and produce a report. Use `task` to delegate research sub-tasks.",
    subagents=load_subagents(str(_HERE / "subagents.yaml")),
    checkpointer=get_saver(),
)
```
The parent plans ("research A, research B, then write"), spawns researcher subagents via the auto-created `task` tool, collects their outputs, and writes the report. Keep subagent system prompts focused; they share the parent's `store`/`backend`.
