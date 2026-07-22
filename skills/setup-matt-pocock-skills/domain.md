# Domain Docs

工程 skills 在探索代码库时应如何消费本仓库的领域文档。

## 探索前先读取这些

- 仓库根目录的 **`CONTEXT.md`**，或
- 如果根目录存在 **`CONTEXT-MAP.md`**，读取它；它指向每个上下文的 `CONTEXT.md`。读取与当前话题相关的每一个。
- **`docs/adr/`**：读取与你即将工作的区域相关的 ADR。在多上下文仓库中，也检查 `src/<context>/docs/adr/` 中的上下文级决策。

如果这些文件不存在，**静默继续**。不要标记它们缺失；不要预先建议创建它们。`/domain-modeling` skill（通过 `/grill-with-docs` 和 `/improve-codebase-architecture` 到达）会在术语或决策真正被解决时懒创建它们。

## 文件结构

单上下文仓库（大多数仓库）：

```text
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

多上下文仓库（根目录存在 `CONTEXT-MAP.md`）：

```text
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← 系统级决策
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← 上下文特定决策
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## 使用 glossary 的词汇

当你的输出命名某个领域概念时（issue 标题、重构建议、假设、测试名称），使用 `CONTEXT.md` 中定义的术语。不要漂移到 glossary 明确避免的同义词。

如果你需要的概念还不在 glossary 中，这是一个信号：要么你正在发明项目不用的语言（重新考虑），要么确实存在缺口（为 `/domain-modeling` 记录它）。

## 标记 ADR 冲突

如果你的输出与现有 ADR 矛盾，要明确指出，而不是静默覆盖：

> _Contradicts ADR-0007 (event-sourced orders) — 但值得重新打开，因为..._
