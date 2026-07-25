---
name: z-implement
description: 选择、执行并验证当前 Zyes ticket。用于调用 z-implement，或用户已批准快速、完整或返工执行。
---

# 执行任务

一次只选择、开始或执行一个 Zyes ticket。

先取得当前 action contract：

```bash
python3 <z-init-skill>/scripts/zyes.py context --entry z-implement [--task <task-directory>] --repo <repo> [<resolution-arguments>] --format prompt
```

按 contract 的 `Action` 执行；`Errors` 非空时停止写入并报告。

- `start-ticket`：有多个候选时先让用户选择。开始前检查工作区；已有改动时把 `git status --short` 和 `git diff HEAD` 文本保存到 Zyes `scratch/review-baselines/<task>/<ticket>/`，并说明 untracked 原始内容无法由 baseline 证明。运行 `zyes.py start-ticket` 后重新取得 contract。
- `implement-ticket`：只读取 contract 的 `Inputs` 和直接相关的代码、规则、glossary/ADR。只实现 current ticket；歧义、spec 冲突或范围扩大时停止。根据风险选择测试与调试方法；用户要求 TDD 或根因不明时按需读取 [TDD profile](references/TDD.md)。
- 完成后填写 ticket 的 Acceptance Criteria、Result 和实际 Verification，再按需读取 [Review profile](references/REVIEW.md)，沿 Standards 与 Spec 双轴检查真实 diff 和可用 baseline。blocking finding 修复并重新验证前保持 `in-progress`；满足条件后运行 `zyes.py complete-ticket`。
- `verify-task`：按需读取 [Verify profile](references/VERIFY.md)，完成任务级双轴验收并写入 result。通过时运行 `accept-task`；blocking finding 通过 `request-changes` 导入返工 ticket；缺少必要人工证据时保持 `verifying`。本 action 不顺手修改产品代码。
- `reverify-or-finish`：仅在用户要求时复验，否则转到 `z-finish-task`。

状态迁移后重新取得 contract。不要自动开始下一个 ticket、归档任务、提交或推送 Git。
