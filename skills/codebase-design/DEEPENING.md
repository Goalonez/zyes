# Deepening

在给定依赖的情况下，如何安全地加深一组 shallow modules。假设已使用 [SKILL.md](SKILL.md) 中的词汇：**module**、**interface**、**seam**、**adapter**。

## Dependency categories

评估一个 deepening 候选项时，对其依赖分类。类别决定加深后的 module 如何跨 seam 测试。

### 1. In-process

纯计算、内存状态、无 I/O。始终可以 deepen：合并 modules，并直接通过新的 interface 测试。不需要 adapter。

### 2. Local-substitutable

拥有本地测试替身的依赖（例如 Postgres 的 PGLite、in-memory filesystem）。如果替身存在，就可以 deepen。加深后的 module 在 test suite 中使用运行中的替身进行测试。seam 是内部的；module 的外部 interface 上没有 port。

### 3. Remote but owned (Ports & Adapters)

你自己的、跨网络边界的服务（microservices、internal APIs）。在 seam 处定义一个 **port**（interface）。deep module 拥有逻辑；transport 作为 **adapter** 注入。测试使用 in-memory adapter。生产使用 HTTP/gRPC/queue adapter。

推荐形状：*“Define a port at the seam, implement an HTTP adapter for production and an in-memory adapter for testing, so the logic sits in one deep module even though it's deployed across a network.”*

### 4. True external (Mock)

你无法控制的第三方服务（Stripe、Twilio 等）。加深后的 module 将外部依赖作为注入的 port；测试提供 mock adapter。

## Seam discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** 除非至少有两个 adapter 是有理由存在的（通常是 production + test），否则不要引入 port。单 adapter seam 只是间接层。
- **Internal seams vs external seams.** 一个 deep module 可以拥有 internal seams（对 implementation 私有，被自己的测试使用），也可以拥有位于 interface 处的 external seam。不要仅仅因为测试使用 internal seams，就把它们暴露到 interface 上。

## Testing strategy: replace, don't layer

- 一旦 deepened module 的 interface 上有测试，shallow modules 上的旧 unit tests 就变成 waste：删除它们。
- 在 deepened module 的 interface 上写新测试。**Interface is the test surface**。
- 测试通过 interface 断言 observable outcomes，而不是 internal state。
- 测试应该经受内部重构：它们描述 behaviour，而不是 implementation。如果 implementation 改变时测试也必须改变，那它测试到了 interface 之后的东西。
