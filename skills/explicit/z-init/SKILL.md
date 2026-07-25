---
name: z-init
description: 初始化或重新配置当前仓库的 Zyes 工作流。用于调用 z-init，或其他 Zyes skill 缺少有效配置。
---

# 设置 Zyes

为当前仓库配置唯一的 Zyes 项目根目录和定位受控块。执行前完整读取 [存储协议](references/STORAGE.md)；任务生命周期由进入对应阶段的 skill 按需读取。

本 skill 只配置存储位置，不创建任务或空的生命周期制品。写入前展示完整草稿并取得用户明确确认；更新已有说明文件时保留受控块之外的内容。

## 1. 探索

从当前目录向上找到仓库根目录，读取：

- 根目录的 `AGENTS.md` 和 `CLAUDE.md`；
- 已有 `<!-- zyes:start -->` 受控块；
- `.zyes/`、已配置外置项目目录及其 `.gitignore`；
- 当前会话可用的全局 `AGENTS.md` 或 `CLAUDE.md` 中的 Zyes home 受控块。

项目说明文件按以下顺序选择：存在 `AGENTS.md` 时使用它；否则使用已有 `CLAUDE.md`；两者都不存在时询问用户要创建哪一个，并推荐 `AGENTS.md`。

## 2. 选择并解析模式

已有有效受控块时优先保持当前模式，并询问是否重新配置；否则让用户选择：

- `shared`：固定使用 `<repo>/.zyes`。
- `external`：使用 `<ZYES_HOME>/<project-name>`，仓库受控块不保存个人绝对路径。

external 模式从对应全局说明文件读取 Zyes home；不存在时询问绝对路径和全局说明文件位置。项目名称默认由仓库目录名规范化为小写 kebab-case。

目标目录已存在但无法证明属于当前仓库时，展示冲突并让用户选择复用或改名，不覆盖。最终 `<ZYES_PROJECT_ROOT>/.gitignore` 至少包含 `/runtime/` 和 `/scratch/`；保留其他规则。external 模式不修改代码仓库的 `.gitignore`。

## 3. 展示并确认

一次性展示：

- 模式和最终绝对项目根目录；
- 要创建或复用的目录；
- 项目说明文件中的 Zyes workflow 受控块；
- external 模式的全局 Zyes home 受控块；
- `<ZYES_PROJECT_ROOT>/.gitignore` 变更。

询问：“是否写入这份 Zyes 配置？回复 `yes` 即可；如需调整，直接说明。”配置变化后重新解析并展示完整草稿。外置路径不在可写范围时另外请求运行环境授权；用户的流程确认不替代权限授权。

## 4. 写入并验证

- 创建 Zyes 项目根目录；其他目录由后续 skill 按实际需要懒创建。
- 新增或原地更新项目受控块，绝不追加重复块。
- external 模式新增或原地更新对应全局 Zyes home 受控块。
- 创建或更新项目根目录中的 `.gitignore`。
- 重新读取所有写入文件，再运行：

```bash
python3 <z-init-skill>/scripts/zyes.py root --repo <repo> [<resolution-arguments>]
```

shared 模式省略 resolution arguments；external 模式传入本次确认的 `--global-instructions <path>` 或 `--zyes-home <absolute-path>`。脚本不可用时按 [存储协议](references/STORAGE.md) 手工执行同等解析，并明确验证方式。

完成时报告模式、项目根目录、修改的说明文件和未执行事项。明确尚未创建任务；external 模式更新全局说明后提示重新开启会话以加载配置。有待处理需求时询问是否进入 `z-brainstorm`，否则停止。
