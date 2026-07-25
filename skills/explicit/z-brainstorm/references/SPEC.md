# Spec profile

只在需求决定收敛且用户批准生成正式规划制品后读取。

- 只写入用户已确认的目标、范围、决定和仓库证据；有阻塞决定时回到 `z-grilling`。
- 保留 `Format version: 2`，使用一个一级标题，并依次填写：`Problem Statement`、`Solution`、`User Stories`、`Acceptance Criteria`、`Decisions`、`Testing Decisions`、`Risks and Deferred Items`、`Out of Scope`、`Further Notes`。
- Decisions 使用唯一连续的 `D-NNN`；Acceptance Criteria 使用唯一连续的 `AC-NNN` 并描述可观察结果。实现与测试决定引用实际 seam，不虚构代码库事实。
- 合并重复内容，移除已解决问题和占位符；风险、推迟项和范围外内容没有时写 `none`。
- 写入当前 task 的 `spec.md` 后重新读取并运行 `zyes.py validate --task <task>`；不要改变 task status。
