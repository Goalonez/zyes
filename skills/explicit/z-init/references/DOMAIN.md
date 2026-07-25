# Zyes 领域文档协议

Zyes 创建和维护的领域文档全部保存在 `<ZYES_PROJECT_ROOT>/knowledge/`。这是所有 Zyes skills 读写领域词汇和 ADR 的唯一位置。

## 文件结构

```text
knowledge/
├── CONTEXT.md
└── adr/
    └── 0001-slug.md
```

目录和文件都按实际内容懒创建。没有领域词汇或 ADR 时静默继续，不预建空文件。

复杂项目和 monorepo 也使用同一份 `knowledge/CONTEXT.md`。按业务区域用小标题组织术语；同一词在不同区域含义不同时，使用带范围的规范名称，不拆分成多套领域文档。

## 探索前读取

1. 按 [STORAGE.md](STORAGE.md) 解析唯一的 Zyes 项目根目录。
2. `knowledge/CONTEXT.md` 存在时读取它。
3. 读取 `knowledge/adr/` 中与工作区域相关的 ADR。

工程 skills 获取 Zyes glossary 和 ADR 时只使用 `knowledge/`。项目规则要求读取的其他工程文档仍按项目规则处理，但不能替代这里的 Zyes 领域真相。

## 使用规则

- 在 spec、ticket、测试名称和评审中使用 glossary 已定义的术语，不要漂移到被明确排除的同义词。
- 如果需要的概念不在 glossary 中，先判断是当前表达不准确，还是领域模型确实缺失；只有后者才按 `z-brainstorm` 的 Domain profile 更新。
- 输出与现有 ADR 冲突时明确指出冲突与重新讨论的原因，不要静默覆盖既有决策。
- `CONTEXT.md` 只记录领域词汇，不保存任务需求、实现计划或运行状态。
