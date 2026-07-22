# Issue tracker: GitHub

本仓库的 issues 和 PRDs 存放为 GitHub issues。所有操作使用 `gh` CLI。

## 约定

- **创建 issue**：`gh issue create --title "..." --body "..."`。多行 body 使用 heredoc。
- **读取 issue**：`gh issue view <number> --comments`，用 `jq` 过滤 comments，并同时获取 labels。
- **列出 issues**：使用适当的 `--label` 和 `--state` filters 调用 `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`。
- **评论 issue**：`gh issue comment <number> --body "..."`
- **添加 / 移除 labels**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **关闭**：`gh issue close <number> --comment "..."`

从 `git remote -v` 推断仓库；在 clone 内运行时 `gh` 会自动完成这件事。

## Pull requests as a triage surface

**PRs as a request surface: no.** _（如果本仓库把外部 PR 当作 feature requests，将其设为 `yes`；`/triage` 会读取这个标志。）_

设为 `yes` 时，PR 会用相同 labels 和 states 流转，并使用 `gh pr` 对应命令：

- **读取 PR**：`gh pr view <number> --comments`，以及用 `gh pr diff <number>` 获取 diff。
- **列出用于 triage 的外部 PRs**：`gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`，然后只保留 `authorAssociation` 为 `CONTRIBUTOR`、`FIRST_TIME_CONTRIBUTOR` 或 `NONE` 的项（丢弃 `OWNER`/`MEMBER`/`COLLABORATOR`）。
- **评论 / label / 关闭**：`gh pr comment`、`gh pr edit --add-label`/`--remove-label`、`gh pr close`。

GitHub 在 issues 和 PRs 间共享同一套编号空间，因此裸 `#42` 可能是任意一种：先用 `gh pr view 42` 解析，失败后回退到 `gh issue view 42`。

## 当 skill 说“publish to the issue tracker”

创建一个 GitHub issue。

## 当 skill 说“fetch the relevant ticket”

运行 `gh issue view <number> --comments`。

## Wayfinding 操作

由 `/wayfinder` 使用。**map** 是一个单独 issue，**child** issues 是 tickets。

- **Map**：一个带 `wayfinder:map` label 的单独 issue，body 保存 Notes / Decisions-so-far / Fog。`gh issue create --label wayfinder:map`。
- **Child ticket**：作为 GitHub sub-issue 链接到 map 的 issue（通过 sub-issues endpoint 调用 `gh api`）。如果 sub-issues 未启用，就把 child 添加到 map body 的 task list，并在 child body 顶部放 `Part of #<map>`。Labels：`wayfinder:<type>`（`research`/`prototype`/`grilling`/`task`）。被认领后，该 ticket 分配给驱动开发者。
- **Blocking**：GitHub 的**原生 issue dependencies**，即规范的、UI 可见的表示。用 `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>` 添加一条边，其中 `<blocker-db-id>` 是 blocker 的数字 **database id**（`gh api repos/<owner>/<repo>/issues/<n> --jq .id`，_不是_ `#number` 或 `node_id`）。GitHub 会报告 `issue_dependencies_summary.blocked_by`（只包含打开的 blockers，也就是实时 gate）。如果 dependencies 不可用，回退到 child body 顶部的 `Blocked by: #<n>, #<n>` 行。当每个 blocker 都关闭时，ticket 解除阻塞。
- **Frontier query**：列出 map 的 open children（`gh issue list --state open`，范围限定为 map 的 sub-issues / task list），丢弃任何有 open blocker（`issue_dependencies_summary.blocked_by > 0`，或 `Blocked by` 行中有 open issue）或 assignee 的项；map 顺序中的第一个胜出。
- **Claim**：`gh issue edit <n> --add-assignee @me`，这是本会话第一次写操作。
- **Resolve**：`gh issue comment <n> --body "<answer>"`，然后 `gh issue close <n>`，然后向 map 的 Decisions-so-far 追加一个 context pointer（gist + link）。
