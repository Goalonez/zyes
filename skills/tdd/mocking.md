# 何时 Mock

只在**系统边界**处 mock：

- 外部 APIs（payment、email 等）
- 数据库（有时；优先使用 test DB）
- 时间/随机性
- 文件系统（有时）

不要 mock：

- 你自己的 classes/modules
- 内部协作者
- 任何你控制的东西

## 为可 Mock 性设计

在系统边界处，设计易于 mock 的接口：

**1. 使用依赖注入**

把外部依赖传入，而不是在内部创建：

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. 优先使用 SDK-style 接口，而不是 generic fetchers**

为每个外部操作创建具体函数，而不是一个带条件逻辑的 generic function：

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK approach 意味着：

- 每个 mock 返回一种具体 shape
- 测试设置里没有条件逻辑
- 更容易看出一个测试触达了哪些 endpoints
- 每个 endpoint 都有类型安全
