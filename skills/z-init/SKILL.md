---
name: z-init
description: 初始化当前仓库的 Zyes 工作流存储位置。用于调用 z-init，或其他 Zyes skill 缺少有效配置时。
---

# 设置 Zyes

为当前仓库确定唯一的 Zyes 项目根目录，并在项目说明文件中写入定位受控块。本 skill 只配置存储位置，不创建任何规划或领域文档。写入前展示完整草稿并取得用户明确确认；更新已有文件时只改动受控块，保留其他内容。

## 目录结构

无论哪种模式，项目根目录结构一致，全部按需懒创建，不预建空目录：

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/          # 进行中的规划：YYYY-MM-DD-slug.md
│   └── done/            # 已完成 / 已取消的规划
└── knowledge/
    ├── CONTEXT.md       # 项目领域词汇（越用越顺手）
    └── adr/             # 承重架构决策：NNNN-slug.md
```

## 1. 探索

从当前目录向上找到仓库根目录，读取：

- 根目录的 `AGENTS.md` 和 `CLAUDE.md`；
- 已有的 `<!-- zyes:start -->` 受控块；
- 当前会话可用的全局 `AGENTS.md` 或 `CLAUDE.md` 中的 Zyes home 受控块。

项目说明文件按以下顺序选择：存在 `AGENTS.md` 时用它；否则用已有 `CLAUDE.md`；两者都没有时询问用户创建哪一个，并推荐 `AGENTS.md`。

## 2. 选择模式

已有有效受控块时优先保持当前模式，并询问是否重新配置；否则让用户选择：

- `shared`：固定使用 `<repo>/.zyes`，随代码仓库一起版本管理。
- `external`：使用 `<ZYES_HOME>/<project-name>`（例如放在个人 Obsidian 库中），仓库受控块不记录个人绝对路径。

external 模式从对应全局说明文件的 Zyes home 受控块读取根目录；不存在时询问绝对路径并写入全局说明文件。项目名称默认由仓库目录名规范化为小写 kebab-case。目标目录已存在但无法确认属于当前仓库时，展示冲突让用户选择复用或改名，不覆盖。

## 3. 展示并确认

一次性展示：模式、最终绝对项目根目录、要写入的项目受控块、external 模式的全局 Zyes home 受控块。询问“是否写入这份 Zyes 配置？回复 `yes` 即可；如需调整，直接说明。”外置路径不在可写范围时另外请求运行环境授权。

## 4. 写入并验证

- shared 模式：默认将 `plans/` 和 `knowledge/` 提交进仓库，以便跨 agent 共享；用户明确不想提交规划时，在 `<repo>/.zyes/.gitignore` 写入 `/plans/`。
- 新增或原地更新受控块，绝不追加重复块；external 模式同时更新全局 Zyes home 受控块。
- 重新读取所有写入的文件确认无误。
- 报告模式、项目根目录、修改的说明文件。external 模式提示重新开启会话以加载全局配置。有待处理需求时询问是否进入 `z-brainstorm`。

## 受控块模板

### Shared

```markdown
<!-- zyes:start -->
## Zyes workflow

- Mode: `shared`
- Root: `.zyes`

需要持久化规划的工作时，使用 Zyes skills，规划文档保存在 `.zyes/plans/`，领域词汇保存在 `.zyes/knowledge/`。
仅当当前代理已安装并能调用 Zyes skills 时使用本节；否则忽略并遵循项目原有流程。
<!-- zyes:end -->
```

### External

```markdown
<!-- zyes:start -->
## Zyes workflow

- Mode: `external`
- Project: `project-name`

从用户的全局 `AGENTS.md`（或 `CLAUDE.md`）读取 Zyes home；项目工作流根目录为 `<ZYES_HOME>/project-name`。
仅当当前代理已安装并能调用 Zyes skills、且能解析个人 Zyes home 时使用本节；否则忽略，不要自动初始化。
<!-- zyes:end -->
```

### 全局 Zyes home（external 模式）

```markdown
<!-- zyes-home:start -->
## Zyes home

Zyes 外置工作流根目录：`/absolute/path/to/zyes-home`。
<!-- zyes-home:end -->
```

项目名称使用小写 kebab-case。同一文件只能有一个对应受控块，更换路径时原地更新。
