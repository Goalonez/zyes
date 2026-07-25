# Zyes

Zyes 是一套面向 AI 编码代理的文档驱动工作流。它把需求、关键决定、任务拆分、实现结果和验证证据保存在本地 Markdown 文件中，让长任务在上下文压缩、会话中断或更换代理后仍然可以可靠继续。

```text
确认需求 → 生成 spec 和 tickets → 逐个实现 → 验收结果 → 归档任务
```

它适合这些场景：

- 需求需要先讨论和收敛，不能直接开始写代码；
- 一个任务需要跨多个会话完成；
- 希望代理一次只处理一个明确的执行切片；
- 需要保留实现结果、测试证据和未完成事项；
- 希望减少每轮对话重复读取无关文档的上下文开销。

## 安装

```bash
npx skills@latest add Goalonez/zyes
```

根据安装器提示选择你的编码代理，并安装仓库中的全部 skills。

运行要求：

- Python 3.10 或更高版本；
- 可以通过 `python3` 调用 Python；
- 不需要安装第三方 Python 依赖。

## 快速开始

### 1. 初始化项目

```text
/z-init 初始化当前项目
```

`z-init` 会检查当前仓库并引导你选择任务制品的保存位置。写入配置前，它会展示完整方案并等待确认。

### 2. 规划任务

```text
/z-brainstorm 为设置页增加主题切换功能
```

`z-brainstorm` 会先调查项目，再逐项确认真正影响行为、范围和验收的决定。确认完成后，它会生成 spec 和可执行 tickets：

- 小任务可以使用单个垂直切片直接进入实现；
- 较大任务会拆成多个具有明确依赖关系的 tickets，并在开始实现前再次等待批准。

需要用户决策时，规划流程会调用内部的逐题追问能力，一次只确认一个问题；能够从代码库查明的事实不会反过来询问用户。

### 3. 实现任务

```text
/z-implement 执行当前任务
```

`z-implement` 一次只处理一个 ticket，并根据当前任务和风险选择适合的测试、调试与检查方式。完成后会保存实际修改、验证结果、已知风险和人工检查项。

最后一个 ticket 完成后，它会根据 spec、tickets 和真实改动执行任务级验收；未通过的项目会形成明确的返工内容，不会被静默忽略。

### 4. 结束任务

```text
/z-finish-task 结束当前任务
```
`z-finish-task` 用于取消、替代或归档终态任务。

### 5. 其他

```text
/z-list-tasks 查看当前任务
/z-handoff 生成当前工作的交接文档
```

`z-list-tasks` 用于跨会话查看当前任务、ticket 进度和下一步；`z-handoff` 在切换代理前保存接手所需的信息；

## 常用入口

| Skill | 用途 |
| --- | --- |
| `/z-init` | 初始化或重新配置当前项目的 Zyes 工作流 |
| `/z-brainstorm <需求>` | 调查项目、确认需求并生成执行计划 |
| `/z-implement` | 选择、实现并验证当前 ticket |
| `/z-list-tasks` | 查看任务状态、进度和下一步 |
| `/z-handoff` | 生成供新会话或其他代理接手的交接文档 |
| `/z-finish-task` | 取消、替代或归档任务 |

`z-grilling` 是规划流程复用的内部基础能力，普通使用不需要单独调用。

## 保存任务制品

初始化时可以选择两种模式：

| 模式 | 保存位置 | 适合场景 |
| --- | --- | --- |
| `shared` | `<repo>/.zyes` | 希望任务制品跟随仓库，由团队共同查看和维护 |
| `external` | `<ZYES_HOME>/<project-name>` | 希望任务制品只保存在个人环境，不进入代码仓库 |

两种模式使用相同的任务结构：

```text
<ZYES_PROJECT_ROOT>/
├── tasks/       # 当前任务、spec、tickets 和验收结果
├── archive/     # 已归档任务
├── knowledge/   # 跨任务复用的领域知识和 ADR
├── artifacts/   # 架构报告和会话交接文档
├── runtime/     # 可重建的当前任务导航状态
└── scratch/     # 可删除的临时检查与返工草稿
```

所有承重信息都保存在可阅读、可审查的 Markdown 文件中，不依赖隐藏数据库。

## 致谢

Zyes 在设计过程中参考了以下项目：

- [mattpocock/skills](https://github.com/mattpocock/skills)
- [Trellis](https://github.com/mindfold-ai/Trellis)

## License

[MIT](LICENSE)
