---
name: z-list-tasks
description: 汇总 Zyes 当前和历史任务、ticket 进度及下一步。用于调用 z-list-tasks 或查询任务状态。
---

# 列出任务

只读汇总当前项目的 Zyes 任务。不要创建任务、修改状态、切换 current 指针或开始实现。

先运行：

```bash
python3 <z-init-skill>/scripts/zyes.py context --entry z-list-tasks --repo <repo> [<resolution-arguments>] --format prompt
```

尚未初始化时说明需要先运行 `z-init`，不代替用户初始化。`Errors` 非空时生成只读异常报告，不修改文件或手工绕过。用户明确要求归档历史时，另运行 `zyes.py list --archive --json`。

用户指定状态、关键词或任务名称时，在取得完整结果后过滤。没有 active task 时直接说明当前没有未归档任务。

按返回顺序输出紧凑表格：

| 字段 | 来源 |
| --- | --- |
| Current | `task.current` |
| Task | `task.title` |
| Status | `task.status` |
| Tickets | `completed/total`，必要时附 `current_ticket` |
| Next | `frontier` 或状态对应动作 |
| Path | `task.path` |

Next 按任务状态给出：

- `planning`：继续 `/z-brainstorm`，完成需求核对和任务文档。
- `ready`：列出 frontier；可以使用 `/z-implement 执行任务「<title>」`。
- `in-progress`：优先列出当前进行中的 ticket；可以使用 `/z-implement 继续任务「<title>」`。
- `verifying`：说明正在验收或等待 `result.md` 中的人工确认项。
- `completed`：说明验收已通过，可以使用 `/z-finish-task 结束任务「<title>」`。
- `cancelled`：显示取消原因，可以使用 `/z-finish-task 归档任务「<title>」`。
- `superseded`：显示替代它的新 task，可以使用 `/z-finish-task 归档任务「<title>」`。

表格后只补充 `errors`、真正影响继续工作的 warning 或阻塞。不要推断缺失字段、自动选择任务、修改 current 或调用下一阶段。
