---
name: improve-codebase-architecture
description: 扫描代码库中的加深机会，将它们呈现为可视化 HTML 报告，然后围绕你选择的候选项进行追问。
disable-model-invocation: true
---

# 改进代码库架构

浮现架构摩擦，并提出**加深机会**：把 shallow modules 变成 deep modules 的重构。目标是可测试性和 AI 可导航性。

这个命令受项目领域模型启发，并建立在一套共享设计词汇之上：

- 运行 `/codebase-design` skill，获取架构词汇（**module**、**interface**、**depth**、**seam**、**adapter**、**leverage**、**locality**）及其原则（deletion test、“interface is the test surface”、“one adapter = hypothetical seam, two = real”）。在每条建议中精确使用这些术语，不要漂移到 “component”、“service”、“API” 或 “boundary”。
- `CONTEXT.md` 中的领域语言为好的 seams 命名；`docs/adr/` 中的 ADR 记录此命令不应重新争论的决策。

## 流程

### 1. 探索

**扫描前先定范围：YAGNI。** 加深一个 module 的收益来自让它未来的变更更容易，因此要对代码库中最近变化过的部分赋予额外权重。先决定*看哪里*，再开始看：

- 如果用户指出了方向，例如一个 module、一个 subsystem、一个痛点，就接受它，并跳过下面的推断。
- 否则，向前回看一段足够长的 commit history（`git log --oneline`），找出代码库的热点，也就是反复出现的文件和区域，并让这些路径首先吸引你的注意。如果变更很分散，没有清晰热点，就扩大范围。

先读取项目的领域 glossary（`CONTEXT.md`）以及你要触碰区域的任何 ADR。

然后使用 Agent tool，并设置 `subagent_type=Explore` 来遍历代码库。不要遵循僵硬的启发式；有机探索，并记录你在哪里感受到摩擦：

- 理解一个概念是否需要在许多小 modules 之间来回跳转？
- 哪些 modules 是 **shallow** 的：interface 几乎和 implementation 一样复杂？
- 哪里只是为了可测试性提取了 pure functions，但真正的 bugs 藏在它们如何被调用之中（没有 **locality**）？
- 哪些紧耦合 modules 会跨过自己的 seams 泄漏？
- 代码库的哪些部分没有测试，或很难通过当前 interface 测试？

对任何你怀疑 shallow 的东西应用 **deletion test**：删除它会集中复杂度，还是只是移动复杂度？“是，会集中”就是你想要的信号。

### 2. 以 HTML 报告展示候选项

将一个自包含 HTML 文件写入操作系统临时目录，避免任何内容落入仓库。临时目录从 `$TMPDIR` 解析，回退到 `/tmp`（Windows 上为 `%TEMP%`），并写到 `<tmpdir>/architecture-review-<timestamp>.html`，这样每次运行都有新文件。为用户打开它：Linux 用 `xdg-open <path>`，macOS 用 `open <path>`，Windows 用 `start <path>`，并告诉用户绝对路径。

报告使用 **Tailwind via CDN** 做布局和样式，并在图/流/序列能可靠表达结构时使用 **Mermaid via CDN** 做图。将 Mermaid 与手写 CSS/SVG 可视化混合使用：当关系是图状（调用图、依赖、序列）时使用 Mermaid；当你想要更 editorial 的表达（mass diagrams、cross-sections、collapse animations）时使用手写 div/SVG。每个候选项都有一个 **before/after visualisation**。要可视化。

每个候选项渲染一张 card，包含：

- **Files**：涉及哪些 files/modules
- **Problem**：为什么当前架构正在造成摩擦
- **Solution**：用 plain English 描述会改变什么
- **Benefits**：用 locality 和 leverage 解释收益，以及测试会如何改善
- **Before / After diagram**：并排展示的自定义图，说明 shallowness 和 deepening
- **Recommendation strength**：`Strong`、`Worth exploring`、`Speculative` 之一，渲染为 badge

报告末尾放一个 **Top recommendation** section：你会先处理哪个候选项，以及为什么。

**领域概念使用 `CONTEXT.md` 词汇，架构概念使用 `/codebase-design` 词汇。** 如果 `CONTEXT.md` 定义了 “Order”，就说 “the Order intake module”，不要说 “the FooBarHandler”，也不要说 “the Order service”。

**ADR 冲突**：如果一个候选项与现有 ADR 矛盾，只有当摩擦真实到值得重新审视该 ADR 时才浮现它。在 card 中清晰标记（例如 warning callout：_“contradicts ADR-0007 — but worth reopening because…”_）。不要列出 ADR 禁止的每个理论性重构。

完整 HTML scaffold、图表模式和样式指导见 [HTML-REPORT.md](HTML-REPORT.md)。

不要现在就提出 interfaces。写完文件后，问用户：“你想探索其中哪一个？”

### 3. 追问循环

一旦用户选择某个候选项，运行 `/grilling` skill，和他们一起走完决策树：约束、依赖、加深后 module 的形状、seam 后面放什么、哪些 tests 能幸存。

当决策逐渐成形时，副作用就地发生：运行 `/domain-modeling` skill，让领域模型保持最新：

- **用 `CONTEXT.md` 中不存在的概念命名一个加深后的 module？** 将该术语添加到 `CONTEXT.md`。如果文件不存在，就懒创建。
- **在对话中打磨了模糊术语？** 当场更新 `CONTEXT.md`。
- **用户用承重理由拒绝候选项？** 提议创建 ADR，表达为：_“要我把这个记录成 ADR 吗？这样未来的架构审查就不会再次建议它。”_ 只有当该理由确实会被未来探索者需要、以避免再次建议同一件事时才提出。临时理由（“现在不值得”）和显而易见的理由跳过。
- **想探索加深后 module 的替代 interfaces？** 运行 `/codebase-design` skill，并使用它的 design-it-twice 并行子代理模式。
