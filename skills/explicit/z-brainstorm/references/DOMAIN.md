# Domain profile

仅在规划出现新领域术语、现有 glossary 冲突，或可能需要 ADR 的承重决定时读取。领域文档只能写入 `<ZYES_PROJECT_ROOT>/knowledge/`。

- 先读取 `knowledge/CONTEXT.md` 和相关 ADR；没有文件时静默继续，只在产生持久内容时懒创建。
- glossary 只记录稳定的业务术语、含义、边界和关系，不写实现细节、任务范围或临时讨论。用户用语与既有定义冲突时指出证据并逐题确认；术语一旦明确就及时更新。
- 用具体边界场景和实际代码交叉核对领域含义；代码与用户意图冲突时交给用户决定，不擅自改写任一方。
- 仅当决定难以反转、缺少上下文会令人意外且确有可行替代方案时，才建议 ADR。用户确认后记录 Context、Decision、Alternatives、Consequences；普通实现选择和临时取舍不建 ADR。
- 更新后重新读取文件，确保没有复制 spec、ticket 或代码可直接恢复的内容。规划中的正式目标与验收仍只写入当前 spec。
