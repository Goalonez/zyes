# Issue tracker: GitLab

本仓库的 issues 和 PRDs 存放为 GitLab issues。所有操作使用 [`glab`](https://gitlab.com/gitlab-org/cli) CLI。

## 约定

- **创建 issue**：`glab issue create --title "..." --description "..."`。多行 description 使用 heredoc。传 `--description -` 会打开编辑器。
- **读取 issue**：`glab issue view <number> --comments`。使用 `-F json` 获取机器可读输出。
- **列出 issues**：使用适当的 `--label` filters 调用 `glab issue list -F json`。
- **评论 issue**：`glab issue note <number> --message "..."`。GitLab 把 comments 称为 “notes”。
- **添加 / 移除 labels**：`glab issue update <number> --label "..."` / `--unlabel "..."`。多个 labels 可以用逗号分隔，也可以重复 flag。
- **关闭**：`glab issue close <number>`。`glab issue close` 不接受关闭 comment，因此先用 `glab issue note <number> --message "..."` 发布解释，再关闭。
- **Merge requests**：GitLab 把 PRs 称为 “merge requests”。使用 `glab mr create`、`glab mr view`、`glab mr note` 等，与 `gh pr ...` 形状相同，只是把 `pr` 换成 `mr`，把 `comment`/`--body` 换成 `note`/`--message`。

从 `git remote -v` 推断仓库；在 clone 内运行时 `glab` 会自动完成这件事。

## Merge requests as a triage surface

**MRs as a request surface: no.** _（如果本仓库把外部 merge requests 当作 feature requests，将其设为 `yes`；`/triage` 会读取这个标志。）_

设为 `yes` 时，MR 会用相同 labels 和 states 流转，并使用 `glab mr` 对应命令：

- **读取 MR**：`glab mr view <number> --comments`，以及用 `glab mr diff <number>` 获取 diff。
- **列出用于 triage 的外部 MRs**：`glab mr list -F json`，然后只保留作者不是项目 member/owner 的 MRs（贡献者的 MR，而不是 maintainer 正在进行的工作）。
- **评论 / label / 关闭**：`glab mr note`、`glab mr update --label`/`--unlabel`、`glab mr close`。

与 GitHub 不同，GitLab 的 issues 和 MRs 分别编号，因此只要知道 maintainer 指的是哪个表面，`#42` 就没有歧义。

## 当 skill 说“publish to the issue tracker”

创建一个 GitLab issue。

## 当 skill 说“fetch the relevant ticket”

运行 `glab issue view <number> --comments`。

## Wayfinding 操作

由 `/wayfinder` 使用。**map** 是一个单独 issue，**child** issues 是 tickets。

- **Map**：一个带 `wayfinder:map` label 的单独 issue，body 保存 Notes / Decisions-so-far / Fog。`glab issue create --label wayfinder:map`。（在有原生 epics 的 GitLab tiers 中，epic 可以承载 map；带 label 的 issue 在任何地方都可用。）
- **Child ticket**：一个 description 顶部带 `Part of #<map>` 的 issue，并带 labels `wayfinder:<type>`（`research`/`prototype`/`grilling`/`task`）。被认领后，该 ticket 分配给驱动开发者。
- **Blocking**：GitLab 的**原生 blocking link**，即规范的、UI 可见的表示。通过作为 note 发布的 `/blocked_by #<n>` quick action 添加（`glab issue note <child> --message "/blocked_by #<blocker>"`）。原生 blocking links 是 Premium/Ultimate 功能；在免费层（或不可用处）回退到 description 顶部的 `Blocked by: #<n>, #<n>` 行。当每个 blocker 都关闭时，ticket 解除阻塞。
- **Frontier query**：`glab issue list -F json`，范围限定为 map 的 children，丢弃任何有 open blocker（指向 open issue 的原生 `blocked_by` link：`glab api projects/:id/issues/:iid/links`，或 `Blocked by` 行中的 open issue）或 assignee 的项；map 顺序中的第一个胜出。
- **Claim**：`glab issue update <n> --assignee @me`，这是本会话第一次写操作。
- **Resolve**：`glab issue note <n> --message "<answer>"`，然后 `glab issue close <n>`，然后向 map 的 Decisions-so-far 追加一个 context pointer（gist + link）。
