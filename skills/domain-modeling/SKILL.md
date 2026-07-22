---
name: domain-modeling
description: 建立并打磨项目的领域模型。适用于用户想明确领域术语或统一语言、记录架构决策，或其他 skill 需要维护领域模型时。
---

# 领域建模

在设计过程中主动建立并打磨项目的领域模型。这是一种*主动*纪律：挑战术语、发明边界场景，并在词汇和决策清晰成形的当下就写入 glossary 和决策记录。（只是为了词汇而*阅读* `CONTEXT.md` 不是这个 skill，那是任何 skill 都可以做的一行习惯。这个 skill 用于你正在改变模型，而不只是消费模型时。）

## 文件结构

大多数仓库只有一个上下文：

```text
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

如果根目录存在 `CONTEXT-MAP.md`，说明仓库有多个上下文。这个 map 指向每个上下文所在位置：

```text
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← 系统级决策
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← 上下文特定决策
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

懒创建文件：只有在有内容可写时才创建。如果不存在 `CONTEXT.md`，就在第一个术语被解决时创建。如果不存在 `docs/adr/`，就在第一个 ADR 被需要时创建。

## 会话期间

### 针对 glossary 挑战术语

当用户使用的术语与 `CONTEXT.md` 中已有语言冲突时，立即指出。“你的 glossary 把 'cancellation' 定义为 X，但你现在似乎指的是 Y，到底是哪一个？”

### 打磨模糊语言

当用户使用含糊或过载的术语时，提出一个精确的规范术语。“你说的是 'account'，你指的是 Customer 还是 User？这两个不是一回事。”

### 讨论具体场景

当正在讨论领域关系时，用具体场景对它们做压力测试。发明能探测边界情况的场景，迫使用户精确说明概念之间的边界。

### 与代码交叉核对

当用户说明某件事如何工作时，检查代码是否同意。如果发现矛盾，把它浮出来：“你的代码会取消整个 Orders，但你刚才说可以部分取消，到底哪一个是对的？”

### 就地更新 CONTEXT.md

当一个术语被解决时，当场更新 `CONTEXT.md`。不要攒到最后，随着它发生就捕获。使用 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) 中的格式。

`CONTEXT.md` 应该完全没有实现细节。不要把 `CONTEXT.md` 当作 spec、草稿纸或实现决策仓库。它只是 glossary，仅此而已。

### 谨慎提出 ADR

只有当以下三点全部为真时，才提议创建 ADR：

1. **难以反转**：以后改变主意的成本有实际意义
2. **没有上下文会令人意外**：未来读者会疑惑“为什么他们要这样做？”
3. **真实权衡的结果**：确实存在可行替代方案，而你基于具体原因选择了其中一个

三者缺一，就跳过 ADR。使用 [ADR-FORMAT.md](./ADR-FORMAT.md) 中的格式。
