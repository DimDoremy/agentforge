# Installing agentforge skills

`agentforge` 的核心交付是 `skills/` 下 5 个 lerdrail 式 skill（纯 Markdown）。两种安装方式，**`npx skills` 为推荐路径**（跨 ZCode / Claude Code / Codex / Cursor 等 70+ agent 通用）。

## 方式 A — `npx skills`（推荐）

[`npx skills`](https://github.com/vercel-labs/skills) 是开放的 agent-skills 安装器（"npm for AI agents"），自动检测你的 coding agent 并把 skill 装到正确位置。

### 全局（所有项目可用）

```bash
npx skills add DimDoremy/agentforge --global
```

把全部 5 个 skill 装到用户级 skills 目录（如 `~/.zcode/skills/`），之后每个新项目都能用。

### 项目本地（仅当前项目）

```bash
# 在你的项目根目录
npx skills add DimDoremy/agentforge
```

装到项目的 skills 目录（如 `.zcode/skills/`）并写一个 `skills-lock.json`，队友拉代码后能得到同一套。把这个 lockfile 提交。

### 只装单个 skill

```bash
npx skills add DimDoremy/agentforge --skill postgres-as-platform --global
```

可装的 skill：`harness-core`、`postgres-as-platform`、`fastapi-serving`、`deepagent-authoring`、`harness-workflow`。不安装只列出：

```bash
npx skills add DimDoremy/agentforge --list
```

### 管理已装 skill

```bash
npx skills list                 # 已装哪些（加 -g 看全局）
npx skills update               # 拉最新
npx skills remove postgres-as-platform -g   # 移除一个
```

> 默认是软链接进 agent 的 skills 目录。加 `--copy` 改为复制文件（便于你直接改）。

> 注：`npx skills` 靠递归扫描 `SKILL.md` 发现 skill，**不**需要 manifest。本仓库的 `skills/` 子目录布局默认就能被发现（实测全部 5 个）。`template/`/`docs/`/`tests/` 等非 skill 内容不含 `SKILL.md`，不会被误装。

## 方式 B — 手动链接 / 拷贝

详见 [`docs/import-guide.md`](docs/import-guide.md)。简言之：把 `skills/<name>` 软链接或拷贝到 agent 的 skills 目录（如 `~/.zcode/skills/<name>`）。

## 装完之后

skill 是只读约定，本身不执行代码。装好后，在新项目里 agent 会：
1. 开工时匹配 `harness-workflow` → 按 harness 工程流程走
2. 用 `harness-core` 的 3 步法添加 agent
3. 持久化/队列/向量/调度决策走 `postgres-as-platform` 的决策矩阵
4. 对外暴露走 `fastapi-serving`；编写 agent 走 `deepagent-authoring`

## 排错

| 现象 | 处理 |
|---|---|
| `npx skills add` 发现少于 5 个 | 某个 skill 的 `description` 过长/过复杂会被发现逻辑跳过——保持 description 简短（细节放 SKILL.md 正文）。本仓库已处理；复现请反馈。 |
| skill 装了但 agent 不触发 | agent 按 `description`（"Use when…"）匹配；确认你的任务表述与触发词对齐。 |
| 想要文件副本而非软链接 | `add` 时加 `--copy`。 |
