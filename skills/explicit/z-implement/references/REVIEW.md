# Review profile

只在已有实际 diff 或完整制品可评估时读取。Review 本身不修改代码、Git 或任务状态。

- 分别检查 **Standards** 与 **Spec**，一个轴通过不能抵消另一个轴的问题。
- 使用仓库规则、实际 diff、spec、当前 ticket/result 和验证证据；只报告可定位、可复现且有影响的 finding。
- finding 标记 `blocking` 或 `advisory`，包含证据、影响和最小修复方向；没有 finding 时明确写 none。
- 有 baseline 时区分 ticket 前改动；untracked 原始内容无法证明时说明范围限制。
- blocking finding 修复并重新验证前不得完成 ticket 或接受 task；advisory 不伪装成阻塞。
