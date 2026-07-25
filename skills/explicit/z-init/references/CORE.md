# Zyes 核心运行协议

本文件只定义所有入口共享的不变量、上下文接口和刷新条件。脚本不可用时才读取 [RECOVERY.md](RECOVERY.md)。

## 解析上下文

优先运行已安装 `z-init` skill 中的协议工具：

```bash
python3 <z-init-skill>/scripts/zyes.py root --repo <repo> [<resolution-arguments>]
python3 <z-init-skill>/scripts/zyes.py context --entry <entry> [--task <task-directory>] --repo <repo> [<resolution-arguments>] --format prompt
```

`entry` 使用 `z-brainstorm`、`z-implement`、`z-list-tasks` 或 `z-finish-task`。需要机器可读结果时改用 `--format json`；两种格式来自同一 action contract。

`resolution arguments` 按项目模式选择：

- `shared`：不传额外参数。
- `external`：传入已经确认的 `--global-instructions <path>` 或 `--zyes-home <absolute-path>`，二者只能选一个。

上层 skill 已经解析 external 参数时，下层 skill 原样复用；已经取得 `project_root` 后，后续只读或状态命令可以改用 `--project-root <ZYES_PROJECT_ROOT>`。不要重新猜测 Zyes home，也不要回退到仓库内创建第二套状态。

命令返回项目根目录、当前状态、下一 action、候选任务、必要输入、frontier、要求、停止点和状态异常：

- `valid: false`：持久化状态异常；停止写入并报告 `errors`。
- `action`：只执行该动作；入口与 task 状态不匹配时按 contract 建议切换入口。
- `budget.oversize: true`：不截断事实；按 `expand` 定向读取或使用 `--verbose` 诊断。
- 用户指定 task 时传入 `--task`。
- 使用返回的绝对 `project_root` 和项目根目录相对路径，不自行解析第二套状态。

脚本报告业务、格式、路径或权限错误时不得绕过。只有 Python 或脚本文件不可用时才读取 [RECOVERY.md](RECOVERY.md)。

## 业务真相与边界

- `task.md` 是任务阶段的唯一来源；`spec.md` 保存需求、范围和已确认决定；单个 ticket 保存切片 status、实际结果和局部验证；`result.md` 只保存任务级验收结论与证据，不重复保存 status。
- `runtime/current.yaml` 只是可重建的导航指针，不保存业务真相。
- 同一 task 最多一个 `in-progress` ticket；不要静默抢占或切换。
- 实现开始后的实质需求变化创建新 planning task，不改写原 spec 或已完成证据。
- 只有当前最新 `Planning revision` 的明确批准可以推进对应检查点。
- Zyes 制品只写入 `<ZYES_PROJECT_ROOT>`；产品文件只由已批准的 ticket 修改。
- 创建、发布、退回规划、执行、返工、验收、取消、替代和归档等状态迁移使用 `zyes.py`，并以命令返回的写后校验结果为准。
- 写命令由 `runtime/.write.lock` 串行化，并在多文件迁移失败时回滚；锁冲突或回滚错误必须报告，不手工补写半迁移状态。
- 入口 skill 只完成 contract 当前 action，不越过用户批准、外部权限或高风险操作确认。

## 上下文读取与刷新

进入 action 后只读取 contract 的 `Inputs`、项目规则和与当前改动直接相关的代码。领域资料存在时只读取相关 glossary 和 ADR；没有领域文件时静默继续。

同一入口已经取得相同 task、`Planning revision`、status 和用户选择下的有效 contract 时可以复用，不重复扫描。发生以下任一变化后重新运行对应入口的 `context`：

- task 或 ticket status 迁移；
- current task、current ticket 或用户选择变化；
- `Planning revision` 变化。

在状态不变时复用有效 context；其他项目资料按当前工作需要读取，不固定加载整个仓库。
