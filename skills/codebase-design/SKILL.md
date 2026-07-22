---
name: codebase-design
description: 用于设计 deep modules 的共享词汇。适用于用户想设计或改进某个 module 的 interface、寻找 deepening opportunities、决定 seam 应该放在哪里、让代码更可测试或更适合 AI 导航，或其他 skill 需要 deep-module 词汇时。
---

# 代码库设计

设计 **deep modules**：在一个小 interface 后面放大量行为，将它放在干净的 seam 上，并能通过这个 interface 测试。只要在设计或重组代码，就使用这套语言和原则。目标是给调用方 leverage、给维护者 locality，并给所有人 testability。

## Glossary

精确使用这些术语，不要替换成 “component”、“service”、“API” 或 “boundary”。一致的语言正是重点。

**Module**：任何拥有 interface 和 implementation 的东西。刻意不限定尺度：可以是 function、class、package，或跨 tier 的 slice。_Avoid_: unit, component, service.

**Interface**：调用方为了正确使用 module 必须知道的一切：type signature，也包括 invariants、ordering constraints、error modes、required configuration 和 performance characteristics。_Avoid_: API, signature（太窄，它们只指 type-level surface）。

**Implementation**：module 内部的东西，也就是它的代码主体。不同于 **Adapter**：一个东西可以是小 adapter、大 implementation（Postgres repo），也可以是大 adapter、小 implementation（in-memory fake）。当话题是 seam 时使用 “adapter”；其他时候使用 “implementation”。

**Depth**：interface 上的 leverage：调用方（或测试）每学习一单位 interface 能行使多少行为。大量行为位于小 interface 后面时，module 是 **deep**；interface 几乎和 implementation 一样复杂时，module 是 **shallow**。

**Seam**（Michael Feathers）：你可以不在某处编辑、却改变该处行为的位置；也就是 module 的 interface 所在的*位置*。seam 放在哪里本身就是一个设计决策，不同于 seam 后面放什么。_Avoid_: boundary（与 DDD 的 bounded context 过载）。

**Adapter**：在 seam 上满足某个 interface 的具体东西。描述的是*角色*（它填的是哪个槽位），不是实体（里面是什么）。

**Leverage**：调用方从 depth 中获得的东西：每学习一单位 interface 得到更多能力。一个 implementation 可以回报 N 个 call sites 和 M 个 tests。

**Locality**：维护者从 depth 中获得的东西：change、bugs、knowledge 和 verification 集中在一个地方，而不是扩散到调用方。修一次，到处都修好。

## Deep vs shallow

**Deep module** = 小 interface + 大量 implementation：

```text
┌─────────────────────┐
│   Small Interface   │  ← 少量 methods，简单 params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← 复杂逻辑被隐藏
│                     │
└─────────────────────┘
```

**Shallow module** = 大 interface + 少量 implementation（避免）：

```text
┌─────────────────────────────────┐
│       Large Interface           │  ← 很多 methods，复杂 params
├─────────────────────────────────┤
│  Thin Implementation            │  ← 只是透传
└─────────────────────────────────┘
```

设计 interface 时，问：

- 我能减少 methods 数量吗？
- 我能简化参数吗？
- 我能把更多复杂度藏到内部吗？

## 原则

- **Depth 是 interface 的属性，不是 implementation 的属性。** 一个 deep module 内部可以由小的、可 mock、可替换的部分组成，只是这些部分不属于 interface。一个 module 可以同时拥有 **internal seams**（对 implementation 私有，被自己的测试使用）以及位于 interface 处的 **external seam**。
- **Deletion test。** 想象删除这个 module。如果复杂度消失了，它只是 pass-through。如果复杂度重新出现在 N 个调用方中，它就在挣自己的位置。
- **Interface is the test surface。** 调用方和测试跨过的是同一个 seam。如果你想测试 interface 之后的东西，这个 module 的形状大概率错了。
- **One adapter means a hypothetical seam. Two adapters means a real one.** 除非某些东西真的会跨 seam 变化，否则不要引入 seam。

## 为 testability 设计

好的 interfaces 会让测试变得自然：

1. **接受依赖，不要创建依赖。**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **返回结果，不要制造 side effects。**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **小 surface area。** 更少 methods = 需要更少 tests。更少 params = 更简单的 test setup。

## 关系

- 一个 **Module** 恰好有一个 **Interface**（它呈现给调用方和测试的 surface）。
- **Depth** 是 **Module** 的属性，针对它的 **Interface** 衡量。
- **Seam** 是 **Module** 的 **Interface** 所在的位置。
- **Adapter** 位于 **Seam** 上，并满足 **Interface**。
- **Depth** 为调用方产生 **Leverage**，为维护者产生 **Locality**。

## 被拒绝的 framing

- **把 depth 当作 implementation 行数与 interface 行数的比例**（Ousterhout）：这会奖励填充 implementation。我们使用 depth-as-leverage。
- **把 “Interface” 当作 TypeScript 的 `interface` 关键字或 class 的 public methods**：太窄。这里的 interface 包含调用方必须知道的每个事实。
- **“Boundary”**：与 DDD 的 bounded context 过载。说 **seam** 或 **interface**。

## 继续深入

- **根据依赖加深一个 cluster**：见 [DEEPENING.md](DEEPENING.md)：dependency categories、seam discipline 和 replace-don't-layer testing。
- **探索替代 interfaces**：见 [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)：启动并行子代理，以几种截然不同的方式设计 interface，然后按 depth、locality 和 seam placement 比较。
