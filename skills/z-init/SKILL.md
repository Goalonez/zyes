---
name: z-init
description: 初始化当前仓库的 Zyes 工作流：选择存储位置、写入项目与全局配置块，并创建工作区骨架。仅在用户明确要求，或其他 Zyes skill 无法解析项目根目录、需要初始化时使用。
disable-model-invocation: true
---

# 初始化 Zyes

确定当前仓库唯一的 Zyes 项目根目录，在项目说明文件中写入定位配置块，将共享规则写入用户的全局说明文件，并创建存储目录骨架。本 skill 配置存储位置，创建基础目录和 `CONTEXT.md` 骨架；计划文档由后续 `z-brainstorm` 创建。写入前展示完整草案并取得用户明确确认；更新已有文件时，仅修改托管块，保留其他内容。

配置分为两部分：项目块保存当前仓库的配置，并标记仓库已启用 Zyes；全局块保存各项目共享的规则，后续统一维护。

## 目录结构

两种模式使用相同布局。初始化只创建基础骨架：`plans/` 下的两个子目录，以及 `CONTEXT.md` 初始文件：

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/                      # 进行中的计划，每份计划一个目录
│   │   └── YYYY-MM-DD-<slug>/       # 由 z-brainstorm 创建
│   │       ├── PLAN.md              # 计划文档
│   │       └── artifacts/           # 可选，供用户手动操作的 Markdown 材料
│   └── done/                        # 已完成或取消的计划，整体目录归档
└── knowledge/                       # 由 z-domain 填充，初始仅有骨架
    └── CONTEXT.md                   # 项目术语表
```

**一份计划对应一个目录**，计划文档固定命名为 `PLAN.md`。简短任务结论和必要人工步骤保留在文档中；人工操作材料需要独立成文时，再创建 `artifacts/`。收尾时整体移动计划目录，保持相对链接有效。初始化仅创建 `plans/active/`、`plans/done/` 和 `knowledge/CONTEXT.md`；具体计划目录、`artifacts/` 和 `knowledge/adr/` 按需创建。

`knowledge/` 初始保持骨架状态，用于明确领域术语的存放位置。[z-domain](../z-domain/SKILL.md) 负责维护内容，在首个术语明确时替换占位内容，在决策符合 ADR 条件时创建 `knowledge/adr/`。

## 根目录锚定规则

Zyes 根目录**始终归属 agent 启动时工作目录（cwd）所在的仓库**。即使用户要求读写其他仓库中的文件，如前后端分仓或多个微服务仓库，也从起始仓库解析 Zyes 配置。跨仓库文件作为外部代码引用，所有 Zyes skill 均遵循此规则。

项目 `zyes` 块中的 `Root` 能解析为具体路径时，配置可用。相对路径按仓库根目录解析；`Root` 包含 `<ZYES_HOME>` 时，使用全局 `zyes-global` 块中的主目录替换。`Mode` 仅用于说明，实际路径由 `Root` 决定。

## 1. 检查配置

从当前目录向上查找仓库根目录，遵循上述锚定规则。查找时仅检查 `.git` 等仓库标识，然后读取本 skill 所需文件：

- 仓库根目录的 `AGENTS.md`；
- 其中已有的 `<!-- zyes:start -->` 托管块；
- 当前会话可用的全局 `AGENTS.md` 中的 `<!-- zyes-global:start -->` 托管块。

读取范围限定在上述路径，直接定位 `AGENTS.md`。初始化只需要说明文件及其托管块；`.env`、凭据、源码、依赖目录和构建产物等无关内容不在读取范围内。

项目配置使用仓库根目录的 `AGENTS.md`；文件缺失时，将创建文件列入草案，等待确认。

共享规则使用当前 agent 的全局 `AGENTS.md`，复用已有 `zyes-global` 块。目标路径不明确时询问用户。

## 2. 选择模式

项目块的 `Root` 已可解析时，优先保留当前模式，并询问是否重新配置。否则请用户选择：

- `shared`：`Root` 为 `.zyes`，工作区位于代码仓库中，供协作者共同使用。
- `external`：`Root` 为 `<ZYES_HOME>/<project-name>`，例如存放于个人 Obsidian 库；仓库配置块保留占位形式。

外部模式从全局 `<!-- zyes-global:start -->` 块读取 Zyes 主目录；缺失时询问绝对路径，并写入全局块。项目名默认使用仓库目录名的小写 kebab-case 形式。目标目录已存在但无法确认归属当前仓库时，展示冲突，请用户选择复用或改名。

## 3. 展示并确认

一次展示：模式、最终项目根目录绝对路径、将创建的目录骨架（`plans/active`、`plans/done` 和 `CONTEXT.md`）、项目托管块、全局托管块及其目标文件路径。使用用户当前对话的语言，请用户确认写入两个文件并创建工作区，也可提出调整意见。取得明确确认后再执行。外部目录超出可写范围时，另行申请运行时授权。

## 4. 写入与验证

- 在项目根目录下创建 `plans/active/`、`plans/done/` 和 `knowledge/CONTEXT.md` 骨架，模板见下文。路径已存在时保留已有内容。
- 在原处添加或更新项目托管块，每个文件只保留一个对应块。
- 两种模式均更新全局块，保留已有主目录路径。
- 重新读取所有写入文件，确认内容正确。
- 汇报模式、项目根目录、新建目录与 `CONTEXT.md`，以及两个修改后的说明文件。提醒用户开启新会话加载全局配置；有待处理需求时，询问是否继续使用 `z-brainstorm`。

## 托管块模板

### 项目块

两种模式结构相同，仅两个配置值不同：

```markdown
<!-- zyes:start -->
## Zyes 工作流

- Mode: `shared`
- Root: `.zyes`

当前仓库已启用 Zyes。共享规则位于用户全局 `AGENTS.md` 的 `zyes-global` 块中。
当前 agent 已安装并可调用 Zyes skills 时使用本节；否则忽略本节，沿用项目现有流程。
<!-- zyes:end -->
```

外部模式仅替换以下配置：

```markdown
- Mode: `external`
- Root: `<ZYES_HOME>/project-name`
```

### 全局块

写入用户的全局 `AGENTS.md`。已知 Zyes 主目录时，保留对应路径行。

```markdown
<!-- zyes-global:start -->
## Zyes 工作流

Zyes external home: `/absolute/path/to/zyes-home`

**当前仓库根目录的 `AGENTS.md` 包含 `<!-- zyes:start -->` 块，且 agent 已安装并可调用 Zyes skills 时，本节生效。** 其他情况忽略本节，由用户明确要求初始化。

从项目块的 `Root` 解析 `<ZYES_PROJECT_ROOT>`：将 `<ZYES_HOME>` 替换为上述主目录，相对路径按仓库根目录解析。

- 仅在用户明确要求使用 Zyes 时启动工作流。计划保存在 `<ZYES_PROJECT_ROOT>/plans/active/<date-slug>/PLAN.md`。同一未完成任务经确认后修订原计划；独立目标或用户要求拆分时另建计划。
- 在 `PLAN.md` 中简记任务，仅在用户需要实际使用时生成额外材料。`artifacts/` 只存放需要独立成文的人工操作材料，例如待手动执行的 SQL；SQL 放在代码块中。
- 执行 Zyes 任务时，读取 `<ZYES_PROJECT_ROOT>/knowledge/CONTEXT.md` 和 `<ZYES_PROJECT_ROOT>/knowledge/adr/` 下的相关 ADR（如存在），沿用已有约定。
<!-- zyes-global:end -->
```

项目名采用小写 kebab-case。每个文件只保留一个对应托管块，变更时原处更新。

## CONTEXT.md 骨架

按下方结构创建 `knowledge/CONTEXT.md`，供后续 skill 写入。标题、说明和占位文字使用用户当前对话的语言。

```markdown
# 项目领域术语

> 项目共享术语，仅记录本项目领域特有的概念。

## 术语

_明确首个领域术语后填写。_
```

“术语”标题用于添加条目，占位行表示术语表尚为空。首次写入术语时，由 [z-domain](../z-domain/SKILL.md) 替换占位内容。
