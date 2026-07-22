---
name: setup-matt-pocock-skills
description: 为工程 skills 配置这个仓库：设置 issue tracker、triage label 词汇和领域文档布局。首次使用其他 engineering skills 前运行一次。
disable-model-invocation: true
---

# 设置 Matt Pocock 的 Skills

搭建 engineering skills 所假设的每仓库配置：

- **Issue tracker**：issues 存放在哪里（默认 GitHub；也原生支持本地 markdown）
- **Triage labels**：五种规范 triage 角色所使用的字符串
- **Domain docs**：`CONTEXT.md` 和 ADR 存放在哪里，以及读取它们的消费规则

这是一个由提示驱动的 skill，不是确定性脚本。先探索，展示你发现的内容，向用户确认，然后写入。

## 流程

### 1. 探索

查看当前仓库，理解它的起始状态。读取已经存在的内容；不要假设：

- `git remote -v` 和 `.git/config`：这是 GitHub 仓库吗？是哪一个？
- 仓库根目录的 `AGENTS.md` 和 `CLAUDE.md`：是否存在？其中是否已经有 `## Agent skills` 章节？
- 仓库根目录的 `CONTEXT.md` 和 `CONTEXT-MAP.md`
- `docs/adr/` 以及任何 `src/*/docs/adr/` 目录
- `docs/agents/`：这个 skill 之前的输出是否已经存在？
- `.scratch/`：说明已经在使用本地 markdown issue tracker 约定
- 是否安装了 `triage` skill？（与本 skill 并列的 `triage` skill 文件夹，或可用 skills 中包含 `triage`。）这决定 Section B 是否完全运行。
- Monorepo 信号：`pnpm-workspace.yaml`、`package.json` 中的 `workspaces` 字段，或一个有自己 `src/` 的非空 `packages/*`。这些只在真正大型多包仓库中出现；它们不存在就意味着单上下文，这几乎适用于所有仓库。

### 2. 展示发现并询问

总结已存在和缺失的内容。然后按顺序处理各 section：一个 section，一个回答，然后下一个。

每个 section 先给出推荐答案，让用户可以用一个词接受。只有当选择确实会分支时，才给一行解释；如果探索已经确定了结果，就完全跳过该 section（`triage` 未安装时跳过 Section B；没有 monorepo 时跳过 Section C）。

**Section A：Issue tracker。**

> 说明：“issue tracker” 是这个仓库中 issues 存放的地方。`to-tickets`、`triage`、`to-spec` 和 `qa` 等 skills 会读取和写入它们，需要知道是调用 `gh issue create`、在 `.scratch/` 下写 markdown 文件，还是遵循你描述的其他工作流。选择你实际用来跟踪这个仓库工作的地方。

默认姿态：这些 skills 是为 GitHub 设计的。如果 `git remote` 指向 GitHub，就提议 GitHub。如果 `git remote` 指向 GitLab（`gitlab.com` 或自托管 host），就提议 GitLab。否则（或用户偏好其他方式），提供：

- **GitHub**：issues 存放在仓库的 GitHub Issues 中（使用 `gh` CLI）
- **GitLab**：issues 存放在仓库的 GitLab Issues 中（使用 [`glab`](https://gitlab.com/gitlab-org/cli) CLI）
- **Local markdown**：issues 作为文件存放在本仓库 `.scratch/<feature>/` 下（适合个人项目或没有 remote 的仓库）
- **Other**（Jira、Linear 等）：让用户用一段话描述工作流；skill 会把它记录为自由格式说明

将选择记录在 `docs/agents/issue-tracker.md`。GitHub 和 GitLab 模板带有一个“PRs/MRs as a request surface” 标志，默认**关闭**。保持关闭且不要主动提出；希望把外部 PR/MR 纳入 triage 队列的用户可以稍后在文件中打开。

**Section B：Triage label 词汇。** 如果未安装 `triage` skill（探索已经告诉你），完全跳过本节：未安装的 skill 不需要 labels。

如果已安装，只问一个问题：

> 你想保留默认 triage labels 吗？（推荐：**yes**）

默认值是五种规范角色，每个 label 字符串等于其名称：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。如果用户回答 **yes**，原样写入。只有当用户回答 no 时，通常是因为 tracker 已经使用其他名称（例如用 `bug:triage` 表示 `needs-triage`），才收集覆盖项，让 `triage` 使用已有 labels，而不是创建重复 labels。

**Section C：Domain docs。** 默认为**单上下文**：仓库根目录一个 `CONTEXT.md` + `docs/adr/`。这适合几乎所有仓库；无需询问，直接写入。

只有在探索发现 monorepo 信号时，才提供**多上下文**：根目录 `CONTEXT-MAP.md` 指向每个上下文的 `CONTEXT.md` 文件。然后确认用户想要哪种布局。

### 3. 确认并编辑

向用户展示草稿：

- 要添加到 `CLAUDE.md` / `AGENTS.md` 中某一个文件的 `## Agent skills` block（选择规则见第 4 步）
- `docs/agents/issue-tracker.md`、`docs/agents/domain.md` 和 `docs/agents/triage-labels.md` 的内容（最后一个仅在安装了 `triage` 时）

写入前允许用户编辑。

### 4. 写入

**选择要编辑的文件：**

- 如果存在 `CLAUDE.md`，编辑它。
- 否则如果存在 `AGENTS.md`，编辑它。
- 如果两者都不存在，询问用户要创建哪一个：不要替他们选择。

当 `CLAUDE.md` 已存在时，绝不创建 `AGENTS.md`（反之亦然）：始终编辑已经存在的那个。

如果所选文件中已经存在 `## Agent skills` block，就原地更新其内容，而不是追加重复 block。不要覆盖周围章节中的用户改动。

该 block：

```markdown
## Agent skills

### Issue tracker

[一行总结 issues 跟踪在哪里]。见 `docs/agents/issue-tracker.md`。

### Triage labels

[一行总结 label 词汇]。见 `docs/agents/triage-labels.md`。

### Domain docs

[一行总结布局：“single-context” 或 “multi-context”]。见 `docs/agents/domain.md`。
```

只有在安装了 `triage` 且 Section B 运行时，才包含 `### Triage labels` 子 block，并写入 `docs/agents/triage-labels.md`。未安装时，两者都省略。

然后以本 skill 文件夹中的种子模板为起点写入 docs 文件：

- [issue-tracker-github.md](./issue-tracker-github.md)：GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md)：GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md)：本地 markdown issue tracker
- [triage-labels.md](./triage-labels.md)：label 映射（仅在安装了 `triage` 时）
- [domain.md](./domain.md)：domain doc 消费规则 + 布局

对于“other” issue trackers，使用用户描述从头写 `docs/agents/issue-tracker.md`。

### 5. 完成

告诉用户 setup 已完成，并说明哪些 engineering skills 现在会读取这些文件。提醒他们之后可以直接编辑 `docs/agents/*.md`；只有当他们想切换 issue tracker 或从头重来时，才需要重新运行此 skill。
