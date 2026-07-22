---
name: to-spec
description: 将当前对话转成 spec，并发布到项目 issue tracker：不访谈，只综合你们已经讨论过的内容。
disable-model-invocation: true
---

此 skill 获取当前对话上下文和对代码库的理解，并生成一份 spec（你可能把这个文档称为 PRD）。不要访谈用户；只综合你已经知道的内容。

issue tracker 和 triage label 词汇应该已经提供给你；如果没有，运行 `/setup-matt-pocock-skills`。

## 流程

1. 如果还没有探索仓库，就探索它，理解代码库当前状态。在整份 spec 中使用项目领域 glossary 的词汇，并尊重你要触碰区域的 ADR。

2. 草拟你将在哪些 seams 上测试这个 feature。优先使用已有 seams，而不是新增。使用尽可能高的 seam。如果需要新 seams，就在你能提出的最高点提出。整个代码库中的 seams 越少越好，理想数量是一个。

向用户确认这些 seams 是否符合他们的预期。

3. 使用下面的模板编写 spec，然后发布到项目 issue tracker。应用 `ready-for-agent` triage label；不需要额外 triage。

<spec-template>

## Problem Statement

用户正面对的问题，从用户视角描述。

## Solution

问题的解决方案，从用户视角描述。

## User Stories

一个很长的编号 user stories 列表。每条 user story 应使用以下格式：

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

这个 user stories 列表应该极其全面，覆盖该 feature 的所有方面。

## Implementation Decisions

已做出的实现决策列表。可以包括：

- 将构建/修改的模块
- 将被修改的模块接口
- 来自开发者的技术澄清
- 架构决策
- Schema changes
- API contracts
- 具体交互

不要包含具体文件路径或代码片段。它们可能很快过时。

例外：如果 prototype 产出的片段比 prose 更精确地编码了某个决策（state machine、reducer、schema、type shape），就在相关决策中内联它，并简短说明它来自 prototype。裁剪到富含决策的部分：不是可工作的 demo，只保留重要片段。

## Testing Decisions

已做出的测试决策列表。包括：

- 什么构成好测试的描述（只测试外部行为，不测试实现细节）
- 将被测试的模块
- 测试的先例（即代码库中相似类型的测试）

## Out of Scope

此 spec 范围之外的事项描述。

## Further Notes

关于该 feature 的任何补充说明。

</spec-template>
