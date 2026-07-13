# agentforge

> 工作流级 AI agent 的开发 harness engineering 包。
> A reusable harness-engineering pack for building small, workflow-level AI agents (AI customer-service, customer research, multi-platform publishing, …) on **FastAPI + LangChain + LangGraph + DeepAgents**, with **uv** for env management and **docker-compose** (split dev/prod) for runtime.

> **快速安装（全局，所有项目可用）：** `npx skills add DimDoremy/agentforge --global`
> 所有安装方式见 [`INSTALL.md`](INSTALL.md)（全局 / 项目本地 / 单个 skill）。

## 这是什么 / What this is

`agentforge` 不是"一个跑着 demo 的单体 app"，而是一个**可引入的 harness engineering 包**，由两层组成：

- **层 A — `skills/`（核心交付）**：5 个 [lerdrail 式](../lerdrail) skill（Markdown `SKILL.md` + YAML front-matter + `references/` 渐进披露）。全局预配置后，可导入到任意新项目的工作目录，指导 agent（如 ZCode）完成"用这套技术栈搭建工作流级 agent"的 harness engineering 规划。
- **层 B — `template/`（可运行骨架）**：一个最小但 `uv sync` / `docker compose` / `pytest` 全绿的代码骨架，新项目以它为起点；skills 描述如何实例化与扩展。

**每个 agent = 一个 `create_deep_agent(...)` 实例**（DeepAgents 作主体），工作流的"步骤/分支"特性通过 tools（=工作流步骤）、skills（=流程文档）、system_prompt（=流程定义）体现，再由 LangGraph Platform runtime + FastAPI 对外暴露。

## 核心架构原则

1. **能用 Postgres 插件提供的，就用 Postgres 插件提供** —— compose 收敛到**单 Postgres 服务**，不再引入 Redis / 向量库 / 独立 broker。
2. **PG 扩展分层**（详见 `docs/postgres-platform.md`）：
   - **Tier 1（dev+prod 默认）**：`pgvector`（RAG/向量）· `pgai`（DB 内 LLM/嵌入）· `pgmq`（任务队列）· `pg_cron`（定时调度）
   - **Tier 2（prod/合规，opt-in）**：PgBouncer · PostgreSQL Anonymizer · PGAudit · wal-g
   - **Tier 3（情境性，仅文档）**：pg_search/ParadeDB（BM25 混合检索）等
3. **每个 agent 是一个可插拔 skill**：添加新工作流 agent 是固定的 3 步法（见 `docs/adding-an-agent.md`），对应 lerdrail "丢一个 `SKILL.md` 目录" 的约定。

## 包含哪些 skill

| Skill 目录 | 主管 |
|---|---|
| [`harness-core`](skills/harness-core/SKILL.md) | 技术栈总览、项目结构、3 步添加 agent 法、PG 平台原则总纲 |
| [`postgres-as-platform`](skills/postgres-as-platform/SKILL.md) | 单 PG 多能力、扩展分层模型、决策矩阵、网络规则 |
| [`fastapi-serving`](skills/fastapi-serving/SKILL.md) | FastAPI + LangGraph runtime 对外暴露 agent |
| [`deepagent-authoring`](skills/deepagent-authoring/SKILL.md) | 用 `create_deep_agent` 编写工作流 agent；工具=工作流步骤 |
| [`agentforge-workflow`](skills/agentforge-workflow/SKILL.md) | harness 工程开发流程编排（脚手架→测试闸→dev/prod→质量闸） |

每个 `SKILL.md` 的 front-matter `description` 以 "Use when…" 开头，是 dispatcher 的路由键；正文保持简短，详情推到 `references/*.md` 按需加载（控 token，与 lerdrail 同构）。

## 如何使用 / How to use

### 作为 skill 包导入新项目

**推荐：用 [`npx skills`](https://github.com/vercel-labs/skills)（跨 ZCode / Claude Code / Codex / Cursor 等 70+ agent）：**

```bash
# 全局：装一次，所有项目可用
npx skills add DimDoremy/agentforge --global

# 或项目本地：只装到当前项目
npx skills add DimDoremy/agentforge

# 或单个 skill：
npx skills add DimDoremy/agentforge --skill postgres-as-platform --global
```

`npx skills` 自动检测你的 agent 并把 skill 装到正确位置（全局如 `~/.zcode/skills/`，项目本地如 `.zcode/skills/`）。完整选项见 [`INSTALL.md`](INSTALL.md)；手动链接/拷贝方式见 [`docs/import-guide.md`](docs/import-guide.md)。

装好后，agent 在新项目里就会按 `agentforge-workflow` 的流程做 harness engineering 规划。

### 直接跑骨架

```bash
cd template
cp .env.example .env        # 填 MODEL / provider key / DB 凭证
docker compose -f docker-compose.dev.yml up
# 另一终端：
curl localhost:8000/agents   # -> [] （骨架初始无 agent）
```

加第一个 agent 后，前端即可：
```bash
curl -X POST localhost:8000/runs/stream -d '{"assistant_id":"<name>","input":{"messages":[{"role":"user","content":"..."}]},"stream_mode":"messages"}'
```

## 项目布局

```
agentforge/
├── README.md            ← 你在这里
├── skills/              ★ 层 A：skill 包（核心）
├── template/            ★ 层 B：可运行代码骨架
├── docs/                架构 / 导入 / 加 agent / PG 平台 / dev-vs-prod / API
└── tests/               验证骨架本身
```

## 关于示例 agent

**main 分支不含任何示例 agent**。客服 / 客户调研 / 多平台发布等具体工作流样例，各自单开 `examples/<name>` 分支展示，作为"加新 skill"的范本。详见 [`docs/adding-an-agent.md`](docs/adding-an-agent.md) 与各 examples 分支的 README。

## 许可证

MIT — 见 [`LICENSE`](LICENSE)。
