---
name: to-tickets
description: 将计划、spec 或当前对话拆成一组 tracer-bullet tickets，每个 ticket 声明其阻塞边，并发布到已配置 tracker：本地以每个 ticket 一个文件中的文本表示边，真实 tracker 上则使用原生 blocking links。
disable-model-invocation: true
---

# To Tickets

将计划、spec 或对话拆成一组 **tickets**：tracer-bullet 垂直切片，每个都声明**阻塞**它的 tickets。

issue tracker 和 triage label 词汇应该已经提供给你；如果没有，运行 `/setup-matt-pocock-skills`。

## 流程

### 1. 收集上下文

使用对话上下文中已有的一切。如果用户把引用（spec 路径、issue number 或 URL）作为参数传入，就获取它并读取完整 body 和 comments。

### 2. 探索代码库（可选）

如果你还没有探索代码库，就探索它，以理解代码当前状态。Ticket 标题和描述应使用项目领域 glossary 的词汇，并尊重你要触碰区域的 ADR。

寻找 prefactor 代码的机会，让实现更容易。“先让改动变容易，再做容易的改动。”

### 3. 草拟垂直切片

将工作拆成 **tracer bullet** tickets。

<vertical-slice-rules>

- 每个切片都切出一条狭窄但完整的路径，贯穿每一层（schema、API、UI、tests）：是垂直切片，不是某一层的水平切片
- 完成的切片本身可以 demo 或验证
- 每个切片大小应适合一个全新的 context window
- 任何 prefactoring 都应先完成

</vertical-slice-rules>

为每个 ticket 给出它的**阻塞边**：必须先完成哪些其他 tickets，它才能开始。没有 blockers 的 ticket 可以立即开始。

**大范围重构是垂直切片的例外。** **大范围重构**是一个机械改动：重命名一列、重新定义一个共享符号类型。它的**爆炸半径**扩散到整个代码库，因此一次编辑会同时打破成千上万个调用点，没有任何垂直切片能以绿色落地。不要强行塞进 tracer bullet；按 **expand–contract** 排序。先 expand：在旧形式旁添加新形式，确保没有东西坏掉。然后按爆炸半径大小分批迁移调用点（按 package、按目录），每批都是自己的 ticket，并被 expand 阻塞；因为旧形式仍然存在，批与批之间 CI 保持绿色。最后 contract：当没有 caller 剩余时删除旧形式，这个 ticket 被每个 migrate batch 阻塞。当连这些 batch 都无法单独保持绿色时，仍保留这个顺序，但让它们共享一个 integration branch，并全部阻塞最终的 integrate-and-verify ticket：绿色只在那里承诺。

### 4. 询问用户

用编号列表展示建议拆分。每个 ticket 展示：

- **Title**：简短描述性名称
- **Blocked by**：必须先完成哪些其他 tickets（如果有）
- **What it delivers**：这个 ticket 让哪个端到端行为可工作

询问用户：

- 粒度感觉是否合适？（太粗 / 太细）
- 阻塞边是否正确：每个 ticket 是否只依赖真正 gate 它的 tickets？
- 是否应该合并或进一步拆分某些 tickets？

迭代，直到用户批准拆分。

### 5. 发布 tickets 到已配置 tracker

发布已批准的 tickets。**如何发布**取决于 `/setup-matt-pocock-skills` 配置的 tracker：tickets 本身相同，只有阻塞边的形态不同：

- **本地文件** → 在 `.scratch/<feature-slug>/issues/<NN>-<slug>.md` 下每个 ticket 写一个文件，按依赖顺序（blockers 在前）从 `01` 编号。每个文件的 “Blocked by” 列出它依赖的编号/标题。使用下面的 per-ticket 文件模板：每个 ticket 一个文件，绝不使用一个合并文件。
- **真实 issue tracker（GitHub、Linear 等）** → 按依赖顺序（blockers 在前）每个 ticket 发布一个 issue，这样每个 ticket 的阻塞边可以引用真实标识符。如果平台有原生 blocking / sub-issue 关系，就使用它；否则将每个 ticket 的 “Blocked by” 设为阻塞 issues。除非另有指示，应用 `ready-for-agent` triage label：这些 tickets 按构造就是 agent 可接手的。

处理 **frontier**：任何 blockers 都完成的 ticket。对纯线性链来说，就是从上到下。

不要关闭或修改任何 parent issue。

<local-ticket-template>

# <NN> — <Ticket title>

**What to build:** 这个 ticket 让哪个端到端行为可工作，从用户视角描述；不要写成逐层实现清单。

**Blocked by:** gate 这个 ticket 的编号/标题，或 “None — can start immediately”。

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

tracker 上 parent issue 的引用（如果来源是已有 issue；否则省略本节）。

## What to build

这个 ticket 让哪个端到端行为可工作，从用户视角描述；不是逐层实现。

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- 每个 blocking ticket 的引用，或 “None — can start immediately”。

</issue-template>

无论哪种形式，都避免具体文件路径或代码片段：它们很快会过时。例外：如果 prototype 产出的片段比 prose 更精确地编码了某个决策（state machine、reducer、schema、type shape），就内联它，并简短说明它来自 prototype。裁剪到富含决策的部分：不是可工作的 demo，只保留重要片段。

使用 `/implement` 一次处理 frontier 中的一个 ticket，并在 tickets 之间清空上下文。
