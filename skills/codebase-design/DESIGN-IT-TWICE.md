# Design It Twice

当用户想为某个已选择的 deepening candidate 探索替代 interfaces 时，使用这个并行子代理模式。它基于 “Design It Twice”（Ousterhout）：你的第一个想法不太可能是最好的。

使用 [SKILL.md](SKILL.md) 中的词汇：**module**、**interface**、**seam**、**adapter**、**leverage**。

## 流程

### 1. 框定问题空间

启动子代理之前，先为所选候选项写一段面向用户的问题空间说明：

- 任何新 interface 都需要满足的约束
- 它会依赖哪些东西，以及这些依赖属于哪个类别（见 [DEEPENING.md](DEEPENING.md)）
- 一个粗略的说明性代码草图，用来让约束具体化：这不是提案，只是让约束更具体的一种方式

把它展示给用户，然后立即进入第 2 步。用户阅读和思考的同时，子代理并行工作。

### 2. 启动子代理

使用 Agent tool 并行启动 3 个以上子代理。每个都必须为加深后的 module 产出一个**截然不同**的 interface。

为每个子代理提供一份独立的技术 brief（文件路径、耦合细节、来自 [DEEPENING.md](DEEPENING.md) 的 dependency category、seam 后面放什么）。这份 brief 独立于第 1 步面向用户的问题空间说明。给每个 agent 一个不同的设计约束：

- Agent 1: “Minimize the interface — aim for 1–3 entry points max. Maximise leverage per entry point.”
- Agent 2: “Maximise flexibility — support many use cases and extension.”
- Agent 3: “Optimise for the most common caller — make the default case trivial.”
- Agent 4（如果适用）: “Design around ports & adapters for cross-seam dependencies.”

在 brief 中同时包含 [SKILL.md](SKILL.md) 词汇和 `CONTEXT.md` 词汇，让每个子代理都用架构语言和项目领域语言一致地命名事物。

每个子代理输出：

1. Interface（types、methods、params，以及 invariants、ordering、error modes）
2. Usage example，展示调用方如何使用它
3. Implementation 在 seam 后面隐藏了什么
4. Dependency strategy 和 adapters（见 [DEEPENING.md](DEEPENING.md)）
5. Trade-offs：哪里 leverage 高，哪里 thin

### 3. 展示和比较

按顺序展示各个设计，让用户能吸收每一个，然后用 prose 比较它们。按 **depth**（interface 上的 leverage）、**locality**（change 集中在哪里）和 **seam placement** 进行对比。

比较后，给出你自己的推荐：你认为哪个设计最强，以及为什么。如果不同设计中的元素适合组合，提出 hybrid。要有立场：用户想要强判断，而不是一份菜单。
