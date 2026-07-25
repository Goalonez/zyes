# Verify profile

只在 task 为 `verifying`，或用户明确要求复验 `completed` task 时读取。本 action 只评估和记录，不修改产品代码。

- 确认全部 tickets 为 completed，Result、Verification、criteria 和未执行检查原因完整。
- 从 ticket 结果与实际 diff 建立交付范围，沿 Standards 与 Spec 双轴 review，再运行与风险匹配的最终验证。
- `result.md` 只写 `Delivered`、`Verification`、`Review Findings`、`Remaining Work`，不保存独立 status。
- 证据完整且无 blocking finding 时运行 `accept-task`；用户要求复验 completed task 时先运行 `reverify-task`。
- blocking finding 写入 result，在 `scratch/` 生成只覆盖既有 spec 的完整 ready ticket 草稿，再运行 `request-changes`。
- 必要人工证据缺失时保持 `verifying`，列出具体检查；简单确认不能代替证据。
