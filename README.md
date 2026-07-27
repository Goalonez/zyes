# Zyes

Zyes 是一套面向 AI 编码代理的文档驱动工作流。它把需求、关键决策、执行步骤、进度和验证证据保存在**单份本地 Markdown 规划文档**中，让长任务在上下文压缩、会话中断或更换代理后仍然可以可靠继续。

```text
确认需求 → 落地一份规划文档 → 逐步执行并记录进度 → 全部完成后收尾
```

它适合这些场景：

- 需求需要先讨论和收敛，不能直接开始写代码；
- 一个任务需要跨多个会话、甚至跨不同 AI agent 完成；
- 希望代理一次只推进一个明确的执行步骤；
- 需要保留决策理由、执行进度和验证证据；
- 希望规划文档本身就是交接件，任何 agent 打开即可接手。

## 设计理念

- **文档即状态**：规划文档的 frontmatter `status`、执行步骤的 checkbox、进度日志共同表达全部状态，不依赖任何数据库或状态机脚本。
- **纯 Markdown、零脚本**：所有 skill 都是纯文本指令，不依赖 Python 或特定 agent 的运行机制，天然可在 Claude Code、Codex、OpenCode 等之间流转。
- **跨 agent 交接**：把规划文档交给任意 agent，只需一句约定——“读规划文档，执行第一个未勾选步骤，勾选并追加进度日志”。

## 安装

```bash
npx skills@latest add Goalonez/zyes
```

根据安装器提示选择你的编码代理，并安装仓库中的全部 skills。无运行时依赖。

## 快速开始

### 1. 初始化项目

```text
/z-init 初始化当前项目
```

`z-init` 引导你选择规划文档的保存位置（`shared` 或 `external`），写入配置前展示完整方案并等待确认。

### 2. 规划需求

```text
/z-brainstorm 为设置页增加主题切换功能
```

`z-brainstorm` 先调查项目，再逐项确认真正影响行为、范围和验收的决策（能从代码查明的事实不反过来问你），最后落地一份规划文档：背景与目标、关键决策、验收标准、执行步骤、进度日志。

### 3. 执行

```text
/z-implement 执行这份规划
```

`z-implement` 一次只推进一个未完成步骤，完成后勾选 checkbox 并在进度日志追加一行（做了什么、验证结果、下一步）。所有步骤完成且验收满足时，顺势收尾：把 `status` 置为 `done` 并移入 `plans/done/`。

### 4. 查看与挑选

```text
/z-list-tasks 查看进行中的规划
```

`z-list-tasks` 列出所有进行中的规划及其进度和下一步，方便跨会话/跨 agent 快速挑一个继续。

## 常用入口

| Skill | 用途 |
| --- | --- |
| `/z-init` | 初始化或重新配置当前项目的存储位置 |
| `/z-brainstorm <需求>` | 调查项目、确认需求并落地规划文档 |
| `/z-implement` | 推进规划中的下一个步骤，完成后收尾 |
| `/z-list-tasks` | 列出进行中的规划、进度和下一步 |

`z-grilling` 是规划流程复用的逐题追问能力，也可单独调用来压力测试任何决策。

## 保存规划文档

初始化时可以选择两种模式：

| 模式 | 保存位置 | 适合场景 |
| --- | --- | --- |
| `shared` | `<repo>/.zyes` | 规划跟随仓库，由团队共同查看维护 |
| `external` | `<ZYES_HOME>/<project-name>` | 规划保存在个人环境（如 Obsidian 库），不进入代码仓库 |

两种模式使用相同结构：

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/     # 进行中的规划：YYYY-MM-DD-slug.md
│   └── done/       # 已完成 / 已取消的规划
└── knowledge/
    ├── CONTEXT.md  # 跨任务复用的领域词汇（越用越顺手）
    └── adr/        # 承重架构决策
```

所有承重信息都保存在可阅读、可审查的 Markdown 文件中。

## 致谢

Zyes 在设计过程中参考了以下项目：

- [mattpocock/skills](https://github.com/mattpocock/skills)
- [Trellis](https://github.com/mindfold-ai/Trellis)

## License

[MIT](LICENSE)
