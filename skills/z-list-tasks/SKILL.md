---
name: z-list-tasks
description: 列出当前项目所有计划文档的状态、进度和下一步。仅在用户明确要求列出计划或查询计划状态时使用。
disable-model-invocation: true
---

# 列出计划

只读汇总当前项目的 Zyes 计划。

从仓库的 `<!-- zyes:start -->` 块解析 `<ZYES_PROJECT_ROOT>`：相对 `Root` 按仓库根目录解析，`<ZYES_HOME>` 从全局 `<!-- zyes-global:start -->` 块替换。始终以 agent 启动时工作目录（cwd）所属的仓库为锚点；跨仓库路径作为外部代码引用，Zyes 根目录仍归属起始仓库。无法解析时，说明当前项目的 Zyes 计划无法定位，并提示用户使用 `z-init`。

## 收集

读取 `<ZYES_PROJECT_ROOT>/plans/active/` 下的全部计划，覆盖两种布局：

- 当前布局：每份计划一个目录，读取 `plans/active/*/PLAN.md`。
- 旧版布局：直接放在目录下的 `plans/active/*.md`，按原位置读取并保留布局。

对每份文档解析：

- front matter 中的 `status`、`created`、`slug`；
- 顶级标题作为计划名称；
- “实施里程碑”（`Implementation Milestones`）中 `- [x]` 的数量及总项数，旧版读取“执行步骤”（`Execution Steps`）；
- “进度日志”（`Progress Log`）最后一行中的下一步；缺失时使用状态对应的默认动作。

用户明确要求查看历史计划时，再读取 `plans/done/`。

## 输出

按 `created` 排序，输出简洁表格：

| 状态 | 标题 | 进度 | 下一步 | 路径 |
| --- | --- | --- | --- | --- |
| `in-progress` | … | 2/5 | 进度日志中的下一步 | plans/active/2026-07-30-slug/PLAN.md |

各状态的默认下一步：

- `planning`：继续使用 `z-brainstorm`，完成需求确认并保存计划。
- `ready`：使用 `z-implement` 开始首个里程碑。
- `in-progress`：使用 `z-implement` 继续下一个未完成里程碑，优先采用进度日志中的下一步。
- `done` / `cancelled`：已收尾，仅在查看历史时列出。

`plans/active/` 为空时，直接说明当前没有活跃计划。表格后仅补充影响继续执行的真实异常，如缺少 front matter 或状态与内容冲突。按文档实际状态汇报，计划选择与执行由用户决定。
