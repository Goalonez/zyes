---
name: z-domain
description: Build and sharpen the project's long-lived domain knowledge — the glossary and architecture decision records. Use when pinning down domain terminology, resolving an overloaded term, or recording a hard-to-reverse decision, including when another Zyes skill needs the domain model maintained.
---

# Maintain domain knowledge

Actively build and sharpen the project's long-lived knowledge: the glossary (`knowledge/CONTEXT.md`) and architecture decision records (`knowledge/adr/`). This is the **active** discipline — challenging terms, surfacing contradictions, and writing things down the moment they crystallise.

Reading `CONTEXT.md` to reuse its vocabulary is the shared baseline across skills. This skill begins when you are **changing** the model.

This knowledge outlives any single plan. A plan document records why *this* task looks the way it does and is archived with it; the glossary and ADRs record what *future* work must respect. Keep the two separate — see "Plan decisions vs ADRs" below.

## Resolving the root and writing into the scaffold

Resolve `<ZYES_PROJECT_ROOT>` from the repo's `<!-- zyes:start -->` block: resolve a relative `Root` against the repo root, or substitute `<ZYES_HOME>` from the global `<!-- zyes-global:start -->` block. Anchor it to the repo of the working directory (cwd) where the agent started; when another Zyes skill already resolved the root, reuse it.

**If the project root cannot be resolved**, ask the user in one line whether to initialize Zyes; if they decline, stop this skill.

```text
<ZYES_PROJECT_ROOT>/knowledge/
├── CONTEXT.md          # the glossary
└── adr/                # created on first qualifying ADR: NNNN-<slug>.md
```

`z-init` creates only the glossary starter; `adr/` may be absent until the first qualifying ADR. An empty scaffold means the domain model is still blank. Handle it as follows:

- **`CONTEXT.md` holding only the starter** — a placeholder line marking the glossary as empty, with or without a `## Language` heading (starters written before this layout omit it): add the heading if it's absent, write the first term under it, delete the placeholder line, and reuse any existing `## Language` heading.
- **`adr/` missing or empty**: create it only when an ADR qualifies; the next ADR is `0001-<slug>.md`.
- **Either one missing** (a workspace initialized before this layout, or one the user pruned): create it when you have something to write.

Whatever the starting state, apply the same writing bar to every entry.

## Output language

Write the glossary and ADRs in the **same language the user is conversing in**. If existing entries or repo docs are clearly in another language, match those instead. Translate the template heading labels into the output language.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately: "the glossary defines X as A, but you seem to mean B — which is it?"

### Sharpen fuzzy language

When the user uses a vague or overloaded term, propose a precise canonical term: "you're saying 'account' — do you mean the customer or the login user? Those are different things."

### Cross-reference with the code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it before recording the claim.

### Write terms down inline

The moment a term is resolved, write it into `CONTEXT.md` right there while the wording and reason are fresh. Use the glossary format below.

Use `CONTEXT.md` as a glossary: domain terms, definitions, and boundaries. Keep task scope and implementation decisions in the plan document.

### Offer ADRs sparingly

An ADR needs a high bar — see "When an ADR qualifies" below. Apply the tests below; when none qualifies, leave the ADR directory absent or unchanged.

## Glossary format

The file heading and the `## Language` section come from the `z-init` starter — leave them in place and add entries under the heading. One entry looks like:

```markdown
**<Term>**:
One or two sentences on what it IS, and its boundary against neighbouring concepts.
_Avoid_: <rejected synonyms>
```

Rules:

- **Be opinionated.** When several words exist for one concept, pick the best and list the rest under `_Avoid_`. A glossary entry needs a clear boundary against neighbouring concepts.
- **Keep definitions tight.** One or two sentences. Define identity and boundary.
- **Only terms specific to this project's domain.** Keep general programming concepts (timeouts, retries, error types, utility patterns) out. Before adding one, ask: is this unique to this project's business, or a general engineering concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge; a flat list is fine otherwise.
- Add a `## Relationships` section only when terms genuinely constrain each other; skip it otherwise.
- When an entry is overturned or a term is retired, **rewrite or delete it in place**.

## ADR format

ADRs live in `<ZYES_PROJECT_ROOT>/knowledge/adr/` with sequential numbering: `0001-<slug>.md`. Create the directory only when writing a qualifying ADR. Scan the directory for the highest existing number and increment by one.

```markdown
# <Short title of the decision>

<1-3 sentences: the context, what was decided, and why.>
```

That's it — an ADR can be a single paragraph. The value is in recording **that** a decision was made and **why**. Add `Considered options` when rejected alternatives are worth remembering, and `Consequences` when downstream effects are non-obvious.

### When an ADR qualifies

All three must be true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Needs context** — a future reader needs the recorded reason to understand why the code works this way.
3. **The result of a real trade-off** — there were genuine alternatives and one was picked for specific reasons.

All three must hold. Reversible choices, obvious implementation moves, and choices with a single viable path stay plan-scoped.

What typically qualifies: architectural shape; integration patterns between modules or systems; technology choices carrying real lock-in; ownership and boundary decisions; deliberate deviations from the obvious path; and constraints invisible in the code (compliance, a partner API's response-time contract).

### Plan decisions vs ADRs

A plan document's "Key Rules" section (or legacy "Key Decisions") already records why that plan looks the way it does, and it is archived together with the plan. Before promoting anything to an ADR, ask:

> Six months from now, could someone changing this area need to know why this choice was made?

When the answer is yes, promote the decision to an ADR. Otherwise keep it plan-scoped. The three tests above still apply — this one only separates plan-scoped decisions from ones that outlive the plan.
