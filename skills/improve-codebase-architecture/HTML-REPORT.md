# HTML 报告格式

架构审查会渲染为操作系统临时目录中的单个自包含 HTML 文件。Tailwind 和 Mermaid 都来自 CDN。Mermaid 能可靠处理图状 diagram；手写 div 和 inline SVG 负责更 editorial 的可视化（mass diagrams、cross-sections）。两者混合使用，不要所有东西都依赖 Mermaid，否则会显得很通用。

## Scaffold

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* small custom layer for things Tailwind doesn't cover cleanly:
         dashed seam lines, hand-drawn-feeling arrow heads, etc. */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

## Header

仓库名、日期，以及一个紧凑图例：实线框 = module，虚线 = seam，红色箭头 = leakage，粗深色框 = deep module。不要介绍段落，直接进入 candidates。

## Candidate card

图承担主要表达。文字稀疏、平实，并自然使用 glossary 术语（来自 `/codebase-design` skill）。

每个候选项是一个 `<article>`：

- **Title**：简短，命名这次 deepening（例如 “Collapse the Order intake pipeline”）。
- **Badge row**：recommendation strength（`Strong` = emerald，`Worth exploring` = amber，`Speculative` = slate），再加一个 dependency category tag（`in-process`、`local-substitutable`、`ports & adapters`、`mock`）。
- **Files**：等宽列表，`font-mono text-sm`。
- **Before / After diagram**：核心内容。两列并排。见下面的 patterns。
- **Problem**：一句话。痛点是什么。
- **Solution**：一句话。会改变什么。
- **Wins**：bullets，每条不超过 6 个词。例如 “Tests hit one interface”、“Pricing logic stops leaking”、“Delete 4 shallow wrappers”。
- **ADR callout**（如果适用）：amber 色调 box 中的一行。

不要写成段落解释。如果 diagram 需要一个段落才能理解，重画 diagram。

## Diagram patterns

选择适合候选项的 pattern。混合使用。不要让每张图看起来都一样，多样性正是重点的一部分。

### Mermaid graph（依赖 / 调用流的主力）

当重点是 “X calls Y calls Z, and look at the mess” 时，使用 Mermaid `flowchart` 或 `graph`。把它包在一个 Tailwind-styled card 里，避免显得像空降进来的。用 classDef 将 leakage edges 着成红色，把 deep module 着成深色。Sequence diagrams 很适合表达 “before: 6 round-trips; after: 1”。

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart LR
      A[OrderHandler] --> B[OrderValidator]
      B --> C[OrderRepo]
      C -.leak.-> D[PricingClient]
      classDef leak stroke:#dc2626,stroke-width:2px;
      class C,D leak
  </pre>
</div>
```

### 手写 boxes-and-arrows（当 Mermaid layout 和你较劲时）

Modules 用带边框和标签的 `<div>`。箭头用 inline SVG `<line>` 或 `<path>`，绝对定位在 relative container 上。当你希望 “after” diagram 像一个粗边框 deep module，内部是灰掉的细节时，用这个；Mermaid 渲染不出正确的重量。

### Cross-section（适合 layered shallowness）

堆叠水平 bands（`h-12 border-l-4`），展示一次调用穿过的 layers。Before：6 个 thin layers，每个都几乎不做事。After：1 个 thick band，标记合并后的 responsibility。

### Mass diagram（适合 “interface as wide as implementation”）

每个 module 两个矩形：一个代表 interface surface area，一个代表 implementation。Before：interface 矩形几乎和 implementation 矩形一样高（shallow）。After：interface 矩形很短，implementation 矩形很高（deep）。

### Call-graph collapse

Before：函数调用树渲染成嵌套 boxes。After：同一棵树折叠成一个 box，现在变成内部调用的部分用淡色展示。

## 样式指导

- 偏 editorial，而不是 corporate-dashboard。留白充足。标题可以使用 serif（`font-serif` 和 stone/slate 搭配不错）。
- 谨慎用色：一个 accent（emerald 或 indigo），再加红色表示 leakage、amber 表示 warnings。
- Diagrams 保持约 320px 高，这样 before/after 能舒适地并排显示，无需滚动。
- Diagram 内的 module labels 使用 `text-xs uppercase tracking-wider`：它们应像 schematic，而不是 UI。
- 唯一脚本是 Tailwind CDN 和 Mermaid ESM import。除此之外报告是静态的：没有 app code，没有 Mermaid 自身渲染之外的交互。

## Top recommendation section

一个更大的 card。Candidate name，一句说明为什么，指向其 card 的 anchor link。就这些。

## 语气

Plain English，简洁；但架构名词和动词直接来自 `/codebase-design` skill。简洁不是术语漂移的借口。

**精确使用：** module、interface、implementation、depth、deep、shallow、seam、adapter、leverage、locality。

**绝不替换为：** component、service、unit（代替 module）· API、signature（代替 interface）· boundary（代替 seam）· layer、wrapper（当你指 module 时）。

**符合风格的措辞：**

- “Order intake module is shallow — interface nearly matches the implementation.”
- “Pricing leaks across the seam.”
- “Deepen: one interface, one place to test.”
- “Two adapters justify the seam: HTTP in prod, in-memory in tests.”

**Wins bullets** 要用 glossary 术语命名收益：*“locality: bugs concentrate in one module”*、*“leverage: one interface, N call sites”*、*“interface shrinks; implementation absorbs the wrappers”*。不要写 *“easier to maintain”* 或 *“cleaner code”*，这些术语不在 glossary 中，也没有赢得位置。

不要犹豫，不要铺垫，不要写 “it's worth noting that...”。如果一个句子可以成为 bullet，就把它变成 bullet。如果一个 bullet 可以删，就删掉。如果一个术语不在 `/codebase-design` glossary 中，在发明新词之前先找一个已有术语。
