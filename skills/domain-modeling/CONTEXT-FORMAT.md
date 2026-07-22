# CONTEXT.md 格式

## 结构

```md
# {上下文名称}

{一到两句话：说明这个上下文是什么，以及它为什么存在。}

## 语言

**Order**:
{一到两句话：描述这个术语}
_Avoid_: Purchase, transaction

**Invoice**:
交付后发送给客户的付款请求。
_Avoid_: Bill, payment request

**Customer**:
下订单的个人或组织。
_Avoid_: Client, buyer, account
```

## 规则

- **要有立场。** 当同一个概念有多个词时，选择最好的一个，并把其他词列在 `_Avoid_` 下。
- **定义保持紧凑。** 最多一到两句话。定义它是什么，而不是它做什么。
- **只包含此项目上下文特有的术语。** 通用编程概念（timeouts、error types、utility patterns）不属于这里，即使项目大量使用它们。添加术语前先问：这是此上下文独有的概念，还是通用编程概念？只有前者属于这里。
- **在自然聚类出现时用小标题分组术语。** 如果所有术语都属于单一内聚区域，扁平列表也可以。

## 单上下文与多上下文仓库

**单上下文（大多数仓库）：** 仓库根目录一个 `CONTEXT.md`。

**多上下文：** 仓库根目录一个 `CONTEXT-MAP.md`，列出上下文、它们所在位置以及彼此关系：

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — 接收并跟踪客户订单
- [Billing](./src/billing/CONTEXT.md) — 生成发票并处理付款
- [Fulfillment](./src/fulfillment/CONTEXT.md) — 管理仓库拣货和发货

## Relationships

- **Ordering → Fulfillment**: Ordering 发出 `OrderPlaced` 事件；Fulfillment 消费它们以开始拣货
- **Fulfillment → Billing**: Fulfillment 发出 `ShipmentDispatched` 事件；Billing 消费它们以生成发票
- **Ordering ↔ Billing**: 共享 `CustomerId` 和 `Money` 类型
```

skill 会推断适用哪种结构：

- 如果存在 `CONTEXT-MAP.md`，读取它以找到上下文
- 如果只存在根目录 `CONTEXT.md`，就是单上下文
- 如果两者都不存在，在第一个术语被解决时懒创建根目录 `CONTEXT.md`

当存在多个上下文时，推断当前话题属于哪一个。如果不清楚，就询问。
