# Issue tracker: Local Markdown

本仓库的 issues 和 specs（你可能把 spec 称为 PRD）存放为 `.scratch/` 中的 markdown 文件。

## 约定

- 每个 feature 一个目录：`.scratch/<feature-slug>/`
- spec 是 `.scratch/<feature-slug>/spec.md`
- 实现 issues 是每个 ticket 一个文件，位于 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 编号；绝不使用一个合并的 tickets 文件
- Triage state 记录在每个 issue 文件顶部附近的 `Status:` 行中（角色字符串见 `triage-labels.md`）
- Comments 和对话历史追加到文件底部的 `## Comments` 标题下

## 当 skill 说“publish to the issue tracker”

在 `.scratch/<feature-slug>/` 下创建一个新文件（必要时创建目录）。

## 当 skill 说“fetch the relevant ticket”

读取引用路径处的文件。用户通常会直接传入路径或 issue number。

## Wayfinding 操作

由 `/wayfinder` 使用。**map** 是一个文件，每个 ticket 一个 **child** 文件。

- **Map**：`.scratch/<effort>/map.md`，body 保存 Notes / Decisions-so-far / Fog。
- **Child ticket**：`.scratch/<effort>/issues/NN-<slug>.md`，从 `01` 编号，问题写在 body 中。`Type:` 行记录 ticket type（`research`/`prototype`/`grilling`/`task`）；`Status:` 行记录 `claimed`/`resolved`。
- **Blocking**：顶部附近的 `Blocked by: NN, NN` 行。当列出的每个文件都是 `resolved` 时，ticket 解除阻塞。
- **Frontier**：扫描 `.scratch/<effort>/issues/`，寻找打开、未阻塞、未认领的文件；按编号排序的第一个胜出。
- **Claim**：在开始任何工作前设置 `Status: claimed` 并保存。
- **Resolve**：在 `## Answer` 标题下追加答案，将 `Status:` 设为 `resolved`，然后向 `map.md` 中 map 的 Decisions-so-far 追加一个 context pointer（gist + link）。
