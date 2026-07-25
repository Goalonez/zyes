---
name: z-finish-task
description: 取消、替代或归档终态 Zyes 任务。用于调用 z-finish-task，或用户明确要求取消、替代或归档任务。
---

# 结束任务

只处理本地任务的取消、替代、终态归档和 current 指针清理，不修改产品代码或执行 Git 交付。

先取得当前 action contract：

```bash
python3 <z-init-skill>/scripts/zyes.py context --entry z-finish-task [--task <task-directory>] --repo <repo> [<resolution-arguments>] --format prompt
```

按 contract 的 `Action` 执行；`Errors` 非空时停止写入并报告。

- `cancel-or-supersede-task`：只有用户明确取消时运行 `zyes.py cancel-task`；只有已有新 task 承接且用户确认替代关系时运行 `zyes.py supersede-task`。普通“结束”不能解释为取消。
- `archive-task`：再次确认用户授权，运行 `zyes.py validate` 和 `zyes.py archive-task`。只能归档 `completed`、`cancelled` 或 `superseded`。
- 其他 action 只报告正确入口或要求用户选择，不强制迁移状态。

完成后报告终态、归档绝对路径和 current 清理结果。不创建提交、不推送，也不开始其他任务。
