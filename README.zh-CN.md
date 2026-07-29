<div align="center">

# Zyes

**面向 AI 编码代理的文档驱动工作流——计划落在 Markdown 文档里，而不是对话里。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made for AI agents](https://img.shields.io/badge/for-AI%20coding%20agents-8A2BE2.svg)](#)

[English](README.md) | 简体中文

</div>

---

长任务最容易崩在上下文被压缩的时刻——计划只存在于对话里，历史一旦被摘要，细节就消失了。换会话或换 agent 会让情况更糟，但压缩才是真正的敌人。

**Zyes 用一份本地 Markdown 文档解决这个问题。** 需求、关键决策、执行步骤和进度全都落在同一份文档里，任何压缩都无法抹去它。没有数据库、没有状态机、没有脚本——文档本身就是状态。
```text
确认需求 → 落地一份规划文档 → 连续执行并记录进度 → 全部完成后收尾
```

## 为什么用 Zyes

- **文档即状态**——规划文档的 frontmatter `status`、步骤 checkbox、进度日志共同表达全部状态，没有任何隐藏信息。
- **抗上下文压缩**——agent 摘要历史时，什么都不会丢失；Markdown 文档始终是唯一的事实来源。
- **纯 Markdown、零脚本**——每个 skill 都是纯文本指令。不依赖 Python、不依赖运行时、不绑定某个 agent 的内部机制。
- **跨会话、跨 agent**——把规划文档交给任意 agent，只需一条约定：*"读规划文档，执行第一个未勾选步骤，勾选并追加进度日志。"*
- **不打扰简单任务**——对一次性小任务 Zyes 会主动让路，交给 agent 直接完成。只有你显式规划、且值得持久化时它才介入。

## 安装

```bash
npx skills@latest add Goalonez/zyes
```

按安装器提示选择你的编码代理并安装全部 skills。无运行时依赖。

## Skills 一览

| Skill | 用途 |
| --- | --- |
| `/z-init` | 选择规划文档的保存位置并接入项目 |
| `/z-brainstorm <需求>` | 调查代码库、确认需求、落地规划文档 |
| `/z-implement` | 推进下一个未完成步骤，全部完成后收尾 |
| `/z-list-tasks` | 列出进行中的规划、进度和下一步 |
| `/z-grilling` | 逐题追问、压力测试任何决策（经实战验证的核心） |

## 快速开始

### 1. 初始化

```text
/z-init 初始化当前项目
```

选择存储模式（`shared` 或 `external`）；写入任何文件前，Zyes 会展示完整方案并等待你确认。

### 2. 规划

```text
/z-brainstorm 为设置页增加主题切换功能
```

`z-brainstorm` 先调查项目，再只确认那些真正影响行为、范围和验收的决策——能从代码查明的事实不会反过来问你。它落地一份规划文档：背景与目标、关键决策、验收标准、执行步骤、进度日志。

> 如果项目还没初始化，Zyes 会**先询问**你是否要启用。你说不，它就让路——不创建任何文件，agent 照常处理你的需求。

### 3. 执行

```text
/z-implement 执行这份规划
```

`z-implement` 默认**连续推进所有未完成步骤**，每完成一步就勾选 checkbox 并在进度日志追加一行（改了什么、验证结果、下一步），只在遇到歧义、冲突、高风险不可逆操作或验证失败时才停下来问你（想逐步确认就说“单步”）。所有步骤完成且验收满足时，顺势收尾：把 `status` 置为 `done` 并移入 `plans/done/`。

### 4. 随处接手

```text
/z-list-tasks
```

列出每一份进行中的规划及其进度和下一步——新会话、或另一个 agent，都能挑一个继续。

## 经实战验证的核心：`z-grilling`

`z-grilling` 是一段经过实战检验的逐题追问提示词（源自 [mattpocock/skills](https://github.com/mattpocock/skills)）。它沿决策树一次只问一个问题，每题都给出推荐答案，能自己查的事实绝不反问，达成共同理解前绝不动手。

`z-brainstorm` 在规划时复用它，但你也可以单独调用它来压力测试*任何*想法：

```text
/z-grilling 帮我压力测试这个架构选择
```

## 规划文档长什么样

```markdown
---
status: in-progress      # planning | ready | in-progress | done | cancelled
created: 2026-07-27
slug: settings-theme-toggle
---
# 为设置页增加主题切换功能

## 背景与目标
用户想要暗色模式。范围：仅设置页。范围外：逐组件主题定制。

## 关键决策
- D1: 选择保存在 localStorage —— v1 无需后端改动。

## 验收标准
- [x] AC1: 切换开关即时把全应用切到亮/暗。
- [ ] AC2: 刷新页面后选择保持。

## 执行步骤
- [x] 1. 增加主题 context + 切换组件。
- [ ] 2. 从 localStorage 持久化并回填选择。

## 进度日志
- 2026-07-27 (会话 A)：完成步骤 1；验证切换可实时改变主题。下一步：持久化。
```

Checkbox 就是步骤状态。进度日志就是交接件——任何 agent 读文档末尾就知道该从哪继续。

## 规划文档保存在哪

初始化时选一种模式：

| 模式 | 位置 | 适合场景 |
| --- | --- | --- |
| `shared` | `<repo>/.zyes` | 规划跟随仓库，团队共享 |
| `external` | `<ZYES_HOME>/<project-name>` | 规划放在个人空间（如 Obsidian 库），不进仓库 |

两种模式结构一致，`/z-init` 会在初始化时把整个骨架建好，开箱即用：

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/     # 进行中的规划：YYYY-MM-DD-slug.md
│   └── done/       # 已完成 / 已取消的规划
└── knowledge/
    ├── CONTEXT.md  # 可复用的领域词汇
    └── adr/        # 承重架构决策
```

所有承重信息都保存在可阅读、可审查的 Markdown 文件中。

## 什么时候*不*该用 Zyes

Zyes 适合多步骤、值得持久化的工作——那种中途丢失上下文就意味着从头再来的任务。对于一次性小改动、纯问答、或 agent 一轮就能搞定的事——跳过它。这些 skill 被刻意收敛过，遇到这类情况会保持安静。

## 致谢

Zyes 在设计过程中参考了：

- [mattpocock/skills](https://github.com/mattpocock/skills)
- [Trellis](https://github.com/mindfold-ai/Trellis)

## License

[MIT](LICENSE)
