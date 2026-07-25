# Tickets profile

只在最新 spec 已确认且用户批准生成执行制品后读取。

- 按可独立验证的 tracer-bullet 垂直切片拆分；快速路径只生成一个完整切片。
- 只声明真实阻塞边；可并行项不互相阻塞，迁移使用 expand-contract 顺序。
- 文件名使用唯一连续的 `<NN>-<slug>.md`。每个 ticket 初始为 `Status: ready`，并填写反引号包裹的 `Spec refs`（至少一个 `AC-NNN`）、`Blocked by`、`What to build`、带 checkbox 的 `Acceptance Criteria`、空的 `Result` 和 `Verification`。
- ticket 只描述本切片的可观察结果、边界和验证，不复制整份 spec，也不预填实现结果。
- 写入全部 tickets 后运行 `zyes.py ready-task --task <task>`。完整路径等待新的执行批准；快速路径只在先前规划批准已明确包含直接执行时进入 `z-implement`。
