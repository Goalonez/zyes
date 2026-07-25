---
name: z-handoff
description: 生成供后续代理或会话接手的 Zyes 交接文档。用于调用 z-handoff 或用户明确要求交接。
---

# 生成交接文档

编写一份交接文档，总结当前对话，让一个新的代理可以继续工作。

先运行 `zyes.py root --repo <repo> [<resolution-arguments>]` 解析项目根目录。尚未初始化时先使用 `z-init`。只有交接内容需要 task、ticket 或 current 状态时，再运行 `zyes.py context --entry z-list-tasks [--task <task-directory>] --project-root <ZYES_PROJECT_ROOT> --format json`，并按返回的 task 路径定向读取 spec、current ticket、result 和直接相关证据；纯对话或非任务工作可以直接交接，不要求存在匹配 task，也不要虚构任务状态。不要把交接文档写入操作系统临时目录、代码仓库中的任意位置或 Zyes 根目录之外。

## 保存位置

保存到：

```text
<ZYES_PROJECT_ROOT>/artifacts/handoffs/handoff-YYYYMMDD-HHMMSS.md
```

时间使用当前项目运行环境的本地时间。目标文件已存在时停止并选择新的时间戳，不覆盖旧交接。创建后重新读取文件，并向用户报告绝对路径。

使用以下固定结构；没有内容的章节写 `none`：

```markdown
# 交接

## 当前状态
任务、task 状态、current ticket 和工作阶段。

## 已完成
本次会话完成的工作及对应持久化制品路径。

## 工作区状态
未提交改动、相关 commit/fixed point，以及无法可靠隔离的范围。

## 验证
实际执行的命令、结果和未验证事项。

## 阻塞与待决定
阻塞、待用户决定事项和风险。

## 下一步
下一项具体动作、建议 skill 和可复制的调用方式。

## 关键路径
spec、tickets、result、ADR 或其他承重制品的本地路径。
```

已经捕获在其他制品中的长内容通过本地路径引用，只提取接手所需的结论和下一步。

遮蔽任何敏感信息，例如 API keys、passwords 或个人身份信息。

如果用户传入了参数，把它们视为下一次会话关注内容的描述，并据此调整文档。
