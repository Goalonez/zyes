# Zyes 任务协议

本协议定义 Zyes 本地任务的最小制品、状态和生命周期。它只规定 skills 之间需要共享的接口，不替代各 skill 的需求分析、领域建模、垂直切片、实现、调试或评审判断。

## 目录

- [任务结构](#任务结构)
- [业务真相](#业务真相)
- [工作流路由](#工作流路由)
- [阶段衔接](#阶段衔接)
- [任务状态](#任务状态)
- [Ticket 状态](#ticket-状态)
- [执行选择规则](#执行选择规则)
- [验收与归档](#验收与归档)
- [取消与替代](#取消与替代)
- [文件模板](#文件模板)

## 任务结构

```text
<ZYES_PROJECT_ROOT>/
├── tasks/
│   └── YYYY-MM-DD-task-slug/
│       ├── task.md
│       ├── spec.md
│       ├── tickets/
│       │   ├── 01-first-slice.md
│       │   └── 02-second-slice.md
│       └── result.md
├── archive/
│   └── YYYY-MM/
│       └── YYYY-MM-DD-task-slug/
├── runtime/
│   └── current.yaml
├── knowledge/                       # 见 DOMAIN.md
├── artifacts/                       # 见 STORAGE.md
└── scratch/                         # 见 STORAGE.md
```

- 任务目录名使用创建日期和小写 kebab-case slug。
- 同名目录已存在时不得追加随机值；让用户选择继续已有任务或输入新名称。
- `task.md` 和 `spec.md` 在任务规划时创建。
- `tickets/` 在用户批准拆分后创建，每个 ticket 一个文件。
- `result.md` 在进入验收时创建；验收未通过时保留失败证据并继续更新。
- 其他制品只在对应 skill 实际需要时创建。

## 业务真相

- `task.md` 是任务阶段的唯一来源。
- `spec.md` 是需求、范围和已确认决策的唯一来源；保持正式规格的表达能力，不把它压缩成状态清单。
- `tickets/*.md` 分别保存垂直切片、阻塞边、验收条件、执行结果和局部验证。
- `result.md` 保存任务级验收结论与证据。
- `runtime/current.yaml` 只是当前任务和 ticket 的导航指针，可以删除并从持久化制品重建。

不要在多个文件重复维护同一状态。任务状态只写入 `task.md`，ticket 状态只写入各自 ticket 文件；`result.md` 不含独立 status，验收结论由正文证据和 task 状态共同表达。

## 工作流路由

按以下顺序使用 skills；只有当前阶段的完成条件满足后才进入下一阶段：

1. `z-brainstorm`：自适应核对需求，推荐快速执行或完整任务路径，并在用户确认后直接落地 spec 与 tickets。
2. 完整任务路径等待用户检查文档并确认执行；快速路径的确认可以同时授权开始执行。
3. `z-implement`：定位任务，选择一个 frontier ticket，将状态设为 `in-progress` 后执行并记录结果。
4. 重复 `z-implement`，直到所有 tickets 都完成。
5. 最后一个 ticket 完成后继续使用 `z-implement` 的 verify action，沿规格与标准两个轴线验收任务并写入 `result.md`。
6. `z-finish-task`：归档已经完成、取消或被新任务替代的终态任务，并清理 current 指针。

spec、tickets、TDD、review、verify 和 domain 能力均由主入口按当前 action 加载短 profile，不再暴露额外兼容入口。

各入口先使用 `scripts/zyes.py context --entry <entry> --format prompt` 获取最小 action contract。状态切换使用 `z-init` skill 中的受控命令，而不是由代理手工同时改多份文件：

- 规划：`create-task`、`ready-task`、`reopen-planning`、`bump-revision`。
- 执行：`start-ticket`、`complete-ticket`。
- 验收：`request-changes`、`reverify-task`、`accept-task`。
- 收尾：`cancel-task`、`supersede-task`、`archive-task`。

写命令以项目级锁串行执行，对多文件迁移做回滚并在成功前校验结果。只有工具文件或 Python 运行时不可用时，才按恢复协议手工执行同等约束。

`z-list-tasks` 是独立的只读导航入口，可以在任意阶段列出未归档任务、ticket 进度和下一步，不改变任务阶段或 current 指针。

## 阶段衔接

当前 skill 完成用户可见阶段或到达需要用户授权的检查点时，如果运行环境支持继续与用户交互，应：

1. 报告当前结果、制品路径和状态。
2. 说明建议进入的下一个 skill 或等待批准的动作。
3. 询问是否继续，并提示“回复 `yes` 即可；如需调整，直接说明”。
4. 等待用户回应，不擅自跨过需要用户批准的检查点。

已经获得授权的内部连续动作不需要重复询问：`z-brainstorm` 可以连续生成 spec 和 tickets，`z-implement` 可以在最后一个 ticket 完成后进入 verify action。只有再次修改产品代码或执行用户未授权的归档等动作时，才建立新的用户可见检查点。

`yes` 是与 Zyes 名称呼应的推荐快捷回复，不是唯一调用方式。用户明确表示“继续”、主动指定下一个 skill，或直接在新的会话中调用它，也可以推进流程；对当前最新检查点明确要求进入下一阶段，本身可以表达批准。下一阶段仍必须重新读取持久化状态并验证自己的实质前置条件，不能跳过未解决的规划问题、尚未批准的 ticket 草案、状态检查或必要验收。

用户提出补充要求、疑问或修改意见时，先处理反馈，不急于推进。如果实现尚未开始，反馈使已批准的目标、范围、验收条件、spec 或 tickets 失效时，运行 `reopen-planning` 将 `ready` task 退回 `planning` 并重新收敛。实现已经开始后，实质变化不得改写原任务：运行 `create-task` 建立新的 planning 任务，再把旧任务标记为 `superseded`。任何较早的批准都不能批准更新后的版本。

每次规划内容发生实质变化、且需要再次向用户展示并确认时，先递增 `Planning revision`，再展示更新后的摘要，避免长对话里把 `yes` 误绑定到旧版本。

任务已经是 `completed` 时，对既有验收证据的质疑使用 `z-implement`：运行 `reverify-task` 将 task 改为 `verifying`，保留并更新原验收正文。超出原 spec 的新要求创建新的 planning 任务，不改写已完成任务。

阶段衔接确认不替代运行环境的权限授权、高风险操作确认或必要的人工验收证据。

## 任务状态

`task.md` 的 `Status` 只使用以下值：

| 状态 | 含义 | 进入条件 |
| --- | --- | --- |
| `planning` | 正在核对需求、生成 spec 或拆分 tickets | 创建任务目录 |
| `ready` | spec 和 tickets 已落地，可以执行 frontier ticket | 所有规划问题已解决，任务制品已生成 |
| `in-progress` | ticket 正在执行，或验收已创建返工 ticket | 开始 ticket 或运行 `request-changes` |
| `verifying` | 所有 tickets 已完成，正在进行任务级验收 | 没有 `ready` 或 `in-progress` ticket |
| `completed` | 验收证据完整且通过，允许归档 | 完整 `result.md` 已写入并运行 `accept-task` |
| `cancelled` | 用户明确停止该任务 | 记录 `Reason`，释放进行中 ticket 并清除 current ticket |
| `superseded` | 实质需求变化由新任务承接 | 记录唯一的 `Superseded by` task 标识 |

正常路径按顺序推进状态。实现开始前可以退回 `planning`；实现开始后的实质变化使用新任务承接并将旧任务设为 `superseded`。验收未通过时退回 `in-progress`，并创建新的返工 ticket，不改写已经完成 ticket 的历史证据。

修改状态时只替换对应的单个 `Status:` 行，保留文件其余内容。无法识别唯一状态行时停止写入并报告格式问题，不要追加第二个状态。

## Ticket 状态

每个 ticket 的 `Status` 只使用以下值：

| 状态 | 含义 |
| --- | --- |
| `ready` | 尚未开始；所有 blockers 完成后进入 frontier |
| `in-progress` | 已开始并正在执行 |
| `completed` | 实现和 ticket 级验证均已完成，等待或已经通过任务级验收 |

Frontier 是所有 `Status: ready` 且 `Blocked by` 中每个 ticket 都为 `completed` 的集合。保留 tracer-bullet 垂直切片和真实阻塞边原则，不为了形成线性队列添加虚假依赖。

`Blocked by` 只接受 `none`，或逗号分隔的本任务 ticket 标识，例如 `01-first-slice, 02-second-slice`。

## 执行选择规则

`z-implement` 在修改产品代码前依次执行：

1. 读取 `task.md`、`spec.md` 和所有 ticket 的 `Status`、`Blocked by`。
2. current 指针已指向合法的 `in-progress` ticket 时继续它，不重复修改状态。
3. 没有 current ticket 时计算 frontier；优先使用用户指定的 ticket，否则选择编号最小的 frontier ticket。
4. 目标 ticket 已是 `in-progress` 但 current 未指向它时，不自动抢占；向用户确认是继续该 ticket，还是释放后重新开始。
5. current 指向另一个未完成 ticket 时，不静默切换；先让用户决定继续、释放或切换。
6. 开始新 ticket 时，将 ticket 和 task 设为 `in-progress`，再写入 current 指针并重新读取验证。

释放未完成 ticket 时只把它改回 `ready` 并清除 current ticket，不丢弃已记录的 Result 或 Verification。共享模式下，ticket 的 `in-progress` 状态就是当前执行信号；同一个 task 同一时间只允许一个代理执行一个 ticket。

`runtime/current.yaml` 使用 Zyes 项目根目录相对路径：

```yaml
task: tasks/YYYY-MM-DD-task-slug
ticket: tasks/YYYY-MM-DD-task-slug/tickets/01-first-slice.md
```

两个路径都必须是规范相对路径，不得包含 `..` 或解析到 Zyes 项目根目录之外；不接受绝对路径。

规划阶段还没有当前 ticket 时，`ticket` 为 `null`。没有当前任务时删除 `current.yaml`，不要保留全空文件。

## 验收与归档

进入任务级验收前确认：

- 所有 tickets 都是 `completed`。
- 每个 ticket 都记录实际实现结果和已执行的验证；未执行的检查明确写明原因。
- 工作区变更与 spec、tickets 的范围一致。

验收必须同时检查规格符合性和工程质量，并把结论写入 `result.md`：

- 未通过：在 `result.md` 保留 blocking findings，在 `scratch/` 写完整的下一个编号 ready ticket 草稿，再运行 `request-changes --ticket-draft <scratch-path>`；命令把草稿移动到任务的 `tickets/` 并将 task 退回 `in-progress`。
- 返工：保留原 ticket 的完成状态和历史证据，只在新 ticket 中记录本轮修复与验证。
- 通过：写完 `result.md` 后运行 `accept-task`，将 task 设为 `completed`。
- 存在无法由代理完成的必要人工检查：保持 task 为 `verifying`，在 `result.md` 明确列出等待用户验证的项目。

返工 tickets 全部完成后，`complete-ticket` 自动把 task 改回 `verifying`。更新 `result.md` 时保留上一轮失败和修复证据。复核已经 `completed` 的任务时先运行 `reverify-task`。

结束任务只做本地生命周期收尾：

1. 确认任务处于 `completed`、`cancelled` 或 `superseded`；`completed` 必须具有完整 `result.md`。
2. 将整个任务目录移动到 `archive/YYYY-MM/`。
3. 如果 current 指针指向该任务，删除 `runtime/current.yaml`。
4. 重新读取归档目录，确认 `task.md`、`spec.md`、tickets 和终态所需证据完整；只有 `completed` 必须存在完整 `result.md`。

归档只移动本地任务制品并清理 current 指针。

## 取消与替代

用户明确放弃工作时：

1. 将当前 `in-progress` ticket 释放为 `ready`。
2. 清除 current ticket。
3. 在 `task.md` 写入 `Status: cancelled` 和单行 `Reason`。
4. 保留已有 spec、tickets、Result 和 Verification，供以后追溯。

实现已经开始后发生实质需求变化时：

1. 创建新的 planning task，重新核对变化后的目标和范围。
2. 将旧任务的当前 ticket 释放为 `ready` 并清除 current ticket。
3. 将旧任务设为 `superseded`，写入新 task 的目录名作为 `Superseded by`；该标识必须唯一指向 `tasks/` 或 `archive/YYYY-MM/` 中可访问的任务目录，不能通过符号链接越出 Zyes 项目根目录。
4. 新任务可以引用旧任务作为背景，但不能继承旧 ticket 的完成状态。

`cancelled` 和 `superseded` 都是终态，可以由 `z-finish-task` 归档；它们不要求所有 tickets completed，也不要求 `result.md`，但不得保留 `in-progress` ticket。

只有原任务目标失效、需要由新 task 承接同一目标的新范围时才使用 `superseded`。如果用户是在原目标之外追加独立需求，创建新的 follow-up planning task，并在新任务的 `spec.md` 中记录与旧任务的关系；不要把旧任务标为 `superseded`。

## 文件模板

### task.md

```markdown
# <Task title>

Status: `planning`
Created: `YYYY-MM-DD`
Planning revision: `1`
```

取消时追加：

```markdown
Reason: 用户决定停止该任务。
```

被替代时追加：

```markdown
Superseded by: `YYYY-MM-DD-new-task-slug`
```

### ticket

```markdown
# <NN> — <Ticket title>

Status: `ready`
Blocked by: `none`

## What to build

<这个切片交付的端到端行为>

## Acceptance Criteria

- [ ] <可观察的验收条件>

## Result

<完成后记录实际实现；开始前保持为空>

## Verification

<完成后记录实际执行的检查及结果；未执行项写明原因>
```

### result.md

```markdown
# 验收结果

## Delivered

<对照 spec 和 tickets 总结实际交付>

## Verification

<命令、手工检查及结果；未执行项写明原因>

## Review Findings

<规格符合性和工程质量发现；没有则写 none>

## Remaining Work

<未完成或后续事项；没有则写 none>
```

`result.md` 不写 `Status`。验收阶段由 `task.md` 的 `verifying` 或 `completed` 表达，阻塞发现和待人工检查分别写入 Review Findings 与 Remaining Work。
