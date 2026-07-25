---
name: z-brainstorm
description: 调查代码库并逐题确认 Zyes 需求，生成执行制品。用于调用 z-brainstorm，或已进入 Zyes 规划与规划调整。
---

# 规划任务

把用户请求转成经过确认的 planning 任务。规划期间可以调查仓库并更新规划制品，不修改产品代码。

先取得当前 action contract：

```bash
python3 <z-init-skill>/scripts/zyes.py context --entry z-brainstorm [--task <task-directory>] --repo <repo> [<resolution-arguments>] --format prompt
```

按 contract 的 `Action` 执行；`Errors` 非空时停止写入并报告。未初始化时使用 `z-init`。

- `create-planning-task`：从请求提取标题和 kebab-case slug，运行 `zyes.py create-task`，再重新取得 contract。创建制品不授权实现。
- `refine-plan`：先调查代码、测试、配置、项目文档及 contract 的 `Inputs`。存在实质性用户决定时使用 `z-grilling`，完整遵循它的一次一问、事实先查、推荐答案和共同理解规则；没有决定时不制造问题。
- 规划涉及新领域术语、glossary 冲突或承重架构决定时，按需读取 [Domain profile](references/DOMAIN.md)；普通任务不固定加载。
- 每次回答实质改变目标、范围、验收条件、测试策略或风险时，更新 spec 草稿并运行 `zyes.py bump-revision`；纯格式或同义改写不递增。
- 决定收敛后展示当前 revision 的 Goal、In Scope、Out of Scope、Acceptance Criteria、Key Decisions、Testing Seams、Risks/Deferred Items，并推荐快速或完整路径。用户只能批准刚展示的 revision。
- 收到规划制品批准后，依次按需读取 [Spec profile](references/SPEC.md) 和 [Tickets profile](references/TICKETS.md)，直接写入并校验正式 spec/tickets。快速路径只生成一个垂直 ticket，并可按这次批准进入 `z-implement`；完整路径生成真实阻塞图后等待新的执行批准。

任何 task 状态、current、用户选择或 planning revision 变化后重新取得 contract。实现开始后的实质范围变化创建新的 planning task，不改写旧 spec 或完成证据。
