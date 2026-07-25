# Zyes 存储协议

## 目录解析

所有 Zyes skills 先从仓库根目录的 `AGENTS.md` 或 `CLAUDE.md` 读取 `## Zyes workflow` 受控块，再解析唯一的 Zyes 项目根目录。

### Shared

```text
<repo>/.zyes/
├── .gitignore
├── tasks/
├── archive/
├── runtime/
├── knowledge/
├── artifacts/
└── scratch/
```

解析结果固定为 `<repo>/.zyes`。

### External

```text
<ZYES_HOME>/
├── project-a/
│   ├── .gitignore
│   ├── tasks/
│   ├── archive/
│   ├── runtime/
│   ├── knowledge/
│   ├── artifacts/
│   └── scratch/
└── project-b/
    ├── .gitignore
    ├── tasks/
    ├── archive/
    ├── runtime/
    ├── knowledge/
    ├── artifacts/
    └── scratch/
```

从用户的全局 `AGENTS.md` 或 `CLAUDE.md` 读取 Zyes home，然后以项目受控块中的 `Project` 拼接：

```text
<ZYES_HOME>/<project-name>
```

不要在项目说明文件中记录 Zyes home 的绝对路径。

解析出的项目根目录不在当前可写范围时，按运行环境的权限机制请求访问；不要静默回退到仓库内目录，也不要创建第二套状态。

## 协议工具

已安装的 `z-init` skill 在 `scripts/zyes.py` 提供无第三方依赖的协议检查和受控状态迁移。

以下命令只解析和报告，不创建目录、不修改状态，也不归档任务：

```bash
python3 <z-init-skill>/scripts/zyes.py root --repo <repo> [<resolution-arguments>]
python3 <z-init-skill>/scripts/zyes.py context --entry <entry> [--task <task-directory>] --repo <repo> [<resolution-arguments>] --format prompt
python3 <z-init-skill>/scripts/zyes.py validate --project-root <ZYES_PROJECT_ROOT> [--task <task-directory>] --json
python3 <z-init-skill>/scripts/zyes.py frontier --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
python3 <z-init-skill>/scripts/zyes.py list --project-root <ZYES_PROJECT_ROOT> [--archive] --json
```

`context --entry` 的 entry 使用 `z-brainstorm`、`z-implement`、`z-list-tasks` 或 `z-finish-task`。它返回入口当前 action 的紧凑 contract；需要机器可读结构时使用 `--format json`。`valid: false` 时停止写入，`budget.oversize: true` 时按 `expand` 定向展开，不能静默截断。

以下命令会修改 Zyes 工作流制品，只在对应用户授权和阶段前置条件满足后使用；命令成功后会重新读取并校验状态：

```bash
python3 <z-init-skill>/scripts/zyes.py create-task --project-root <ZYES_PROJECT_ROOT> --title <title> --slug <slug> [--date YYYY-MM-DD] --json
python3 <z-init-skill>/scripts/zyes.py ready-task --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
python3 <z-init-skill>/scripts/zyes.py reopen-planning --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
python3 <z-init-skill>/scripts/zyes.py bump-revision --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
python3 <z-init-skill>/scripts/zyes.py start-ticket --project-root <ZYES_PROJECT_ROOT> --task <task-directory> [--ticket <ticket-id>] --json
python3 <z-init-skill>/scripts/zyes.py complete-ticket --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --ticket <ticket-id> --json
python3 <z-init-skill>/scripts/zyes.py request-changes --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --ticket-draft <scratch-ticket-path> --json
python3 <z-init-skill>/scripts/zyes.py reverify-task --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
python3 <z-init-skill>/scripts/zyes.py accept-task --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
python3 <z-init-skill>/scripts/zyes.py cancel-task --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --reason <reason> --json
python3 <z-init-skill>/scripts/zyes.py supersede-task --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --replacement <new-task-directory> --json
python3 <z-init-skill>/scripts/zyes.py archive-task --project-root <ZYES_PROJECT_ROOT> --task <task-directory> --json
```

每个写命令使用项目级非阻塞锁 `runtime/.write.lock`，对多文件写入、移动和 current 更新执行事务回滚，再做写后校验。同一项目已有写命令运行时等待后重试，不并发绕过。锁文件和 `current.yaml` 一样属于可删除 runtime；只有确认没有写命令运行时才可清理锁文件。

`root` 命令同样在 `--repo <repo>` 后接受 `[<resolution-arguments>]`。shared 模式省略；external 模式传入已经确认的 `--global-instructions <path>` 或 `--zyes-home <absolute-path>`，二者只能选一个。上层 skill 已解析参数时下层原样复用。命令以非零状态退出时保留输出并报告具体异常，不要绕过错误继续修改状态。日常阶段的统一模板和刷新条件见 [CORE.md](CORE.md)。

## 目录语义

- `tasks/`：未归档任务的持久化制品；它是任务状态的来源。
- `archive/`：已结束任务；按 `YYYY-MM/` 分组。
- `runtime/`：可删除、可重建的 `current.yaml` 导航和 `.write.lock`；不得保存需求、验收结果或其他业务真相。具体导航字段见 [TASKS.md](TASKS.md)。
- `knowledge/`：Zyes 创建和维护的领域词汇与 ADR；具体结构和读取规则见 [DOMAIN.md](DOMAIN.md)。
- `artifacts/`：需要跨会话保留的非任务制品，例如架构报告和交接文档。
- `scratch/`：一次性反馈文件、临时 harness、原始 trace、返工 ticket 草稿和 ticket review baseline 等可删除工作文件；不得保存唯一的需求、决策或验收证据。返工草稿由 `request-changes` 校验并移动到任务目录后才成为持久化 ticket。

`knowledge/`、`artifacts/` 和 `scratch/` 都按实际使用懒创建，不预建空目录。`artifacts/` 使用以下固定分类：

```text
artifacts/
├── architecture/
└── handoffs/
```

实现和调试中形成的长期事实与回归证据写入对应 ticket 的 Result 和 Verification；一次性实验材料留在 `scratch/`。持久化任何外部输入前先脱敏。

## 写入边界

除以下两类明确例外，Zyes skills 创建、复制、移动或更新的所有工作流文件都必须位于唯一的 `<ZYES_PROJECT_ROOT>` 内：

1. `z-init` 在项目级和全局 `AGENTS.md` 或 `CLAUDE.md` 中维护的 Zyes 受控定位块。
2. `z-implement` 按已批准 ticket 修改的产品源码、测试、配置、schema、migration 和项目文档。

项目原生测试、构建或代码生成命令产生的缓存与输出由项目规则管理，不是 Zyes 工作流制品。

每次写入工作流制品前，先规范化目标路径并确认：

- 目标位于解析后的 `<ZYES_PROJECT_ROOT>` 内。
- 相对路径不含 `..`，且不能通过符号链接逃逸项目根目录。
- 不使用操作系统临时目录、当前工作目录中的临时子目录或其他隐式回退位置。
- 目标目录已有未知文件时不覆盖；先读取并按对应 skill 的冲突规则处理。

无法解析唯一项目根目录、目标越界或外置根目录不可写时停止，并按运行环境权限机制请求访问；不要回退到仓库或系统临时目录创建第二套状态。

两种模式都在 `<ZYES_PROJECT_ROOT>/.gitignore` 中至少包含：

```gitignore
/runtime/
/scratch/
```

文件不存在时由 `z-init` 创建，存在时保留已有其他规则。external 模式更新外置项目目录自己的 `.gitignore`，不修改代码仓库的 `.gitignore`。

## 项目说明受控块

优先写入项目根目录 `AGENTS.md`；只有 `CLAUDE.md` 时写入它。

### Shared 模板

```markdown
<!-- zyes:start -->
## Zyes workflow

- Mode: `shared`
- Root: `.zyes`

处理需要持久化规划或执行状态的工作时，使用 Zyes skills，并将任务制品保存在上述目录。
仅当当前代理已安装并能够调用 Zyes skills 时使用本节；未安装时忽略本节并继续遵循项目原有流程。
<!-- zyes:end -->
```

### External 模板

```markdown
<!-- zyes:start -->
## Zyes workflow

- Mode: `external`
- Project: `project-name`

从用户的全局 `AGENTS.md` 读取 Zyes home；如果本项目只有 `CLAUDE.md`，则读取全局 `CLAUDE.md`。项目工作流目录为 `<ZYES_HOME>/project-name`。
仅当当前代理已安装并能够调用 Zyes skills 时使用本节；未安装或无法解析个人 Zyes home 时忽略本节，不要自动初始化或修改项目。
<!-- zyes:end -->
```

项目名称使用小写 kebab-case。项目目录已存在但无法确认属于当前仓库时，必须让用户决定复用还是改名。

## 全局说明受控块

External 模式使用。全局说明文件类型应与项目入口一致：项目使用 `AGENTS.md` 时写全局 `AGENTS.md`；项目只有 `CLAUDE.md` 时写全局 `CLAUDE.md`。

```markdown
<!-- zyes-home:start -->
## Zyes home

Zyes 外置工作流根目录：`/absolute/path/to/zyes-home`。
<!-- zyes-home:end -->
```

同一文件只能有一个 Zyes home 受控块。更换路径时原地更新。
