---
name: z-domain
description: Build and sharpen the project's long-lived domain knowledge — the glossary and architecture decision records. Use when pinning down domain terminology, resolving an overloaded term, or recording a hard-to-reverse decision, including when another Zyes skill needs the domain model maintained.
---

# Maintain domain knowledge

Actively build and sharpen the project's long-lived knowledge: the glossary (`knowledge/CONTEXT.md`) and architecture decision records (`knowledge/adr/`). This is the **active** discipline — challenging terms, surfacing contradictions, and writing things down the moment they crystallise.

Merely **reading** `CONTEXT.md` to reuse its vocabulary is not this skill — that's a one-line habit any skill does. This skill is for when you are **changing** the model.

This knowledge outlives any single plan. A plan document records why *this* task looks the way it does and is archived with it; the glossary and ADRs record what *future* work must respect. Keep the two separate — see "Plan decisions vs ADRs" below.

## Resolving the root and writing into the scaffold

Resolve the Zyes project root the same way as the other skills: read the `<!-- zyes:start -->` managed block in the repo's `AGENTS.md`/`CLAUDE.md`, anchored to the repo of the working directory (cwd) where the agent started. When invoked by another Zyes skill that already resolved the root, reuse it.

**Do not auto-initialize when no valid config is detected.** Ask the user in one line whether to initialize Zyes; if they decline, **stop this skill** and create no files.

```text
<ZYES_PROJECT_ROOT>/knowledge/
├── CONTEXT.md          # the glossary
└── adr/                # NNNN-<slug>.md
```

`z-init` scaffolds both up front, so **expect them to already exist and to be empty**. An empty scaffold is not a signal that nothing belongs here — it only means nothing has been recorded yet. Handle it as follows:

- **`CONTEXT.md` holding only the starter** — a placeholder line such as `_No entries yet._`, with or without a `## Language` heading (starters written before this layout omit it): add the heading if it's absent, write the first term under it, and **delete the placeholder line**. Never leave the placeholder stranded above real entries, and never append a second `## Language` heading.
- **`adr/` empty**: the next ADR is `0001-<slug>.md`.
- **Either one missing** (a workspace initialized before this layout, or one the user pruned): create it when you have something to write, and never scaffold it empty in advance.

Whatever the starting state, the bar for writing is unchanged — an empty file is never a reason to lower it, and a populated one is never a reason to stop.

## Output language

Write the glossary and ADRs in the **same language the user is conversing in**. If existing entries or repo docs are clearly in another language, match those instead. Headings in the templates below are labels to translate, not literal strings to copy.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately: "the glossary defines X as A, but you seem to mean B — which is it?"

### Sharpen fuzzy language

When the user uses a vague or overloaded term, propose a precise canonical term: "you're saying 'account' — do you mean the customer or the login user? Those are different things."

### Cross-reference with the code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it rather than silently recording the claim.

### Write terms down inline

The moment a term is resolved, write it into `CONTEXT.md` right there. **Don't batch these up to the end of the task** — by then the wording has drifted and the reason is gone. Use the glossary format below.

`CONTEXT.md` is a glossary and nothing else. It must be totally free of implementation details. Do not treat it as a spec, a scratch pad, or a home for task scope or implementation decisions.

### Offer ADRs sparingly

An ADR needs a high bar — see "When an ADR qualifies" below. **Most tasks produce zero ADRs, and that is the intended shape.** Don't go looking for one to justify.

## Glossary format

The file heading and the `## Language` section come from the `z-init` starter — leave them in place and add entries under the heading. One entry looks like:

```markdown
**<Term>**:
One or two sentences on what it IS, and its boundary against neighbouring concepts.
_Avoid_: <rejected synonyms>
```

Rules:

- **Be opinionated.** When several words exist for one concept, pick the best and list the rest under `_Avoid_`. If you can't say what the term is being distinguished *from*, you don't have a glossary entry yet — you have a description. Leave it out.
- **Keep definitions tight.** One or two sentences. Define what it is, not what it does.
- **Only terms specific to this project's domain.** General programming concepts (timeouts, retries, error types, utility patterns) don't belong even if the project leans on them heavily. Before adding one, ask: is this unique to this project's business, or a general engineering concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge; a flat list is fine otherwise.
- Add a `## Relationships` section only when terms genuinely constrain each other; skip it otherwise.
- When an entry is overturned or a term is retired, **rewrite or delete it in place** — never append a competing definition.

## ADR format

ADRs live in `<ZYES_PROJECT_ROOT>/knowledge/adr/` with sequential numbering: `0001-<slug>.md`. Scan the directory for the highest existing number and increment by one.

```markdown
# <Short title of the decision>

<1-3 sentences: the context, what was decided, and why.>
```

That's it — an ADR can be a single paragraph. The value is in recording **that** a decision was made and **why**, not in filling out sections. Add `Considered options` only when the rejected alternatives are worth remembering, and `Consequences` only when there are non-obvious downstream effects. Most ADRs need neither.

### When an ADR qualifies

All three must be true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Surprising without context** — a future reader will look at the code and wonder "why on earth was it done this way?"
3. **The result of a real trade-off** — there were genuine alternatives and one was picked for specific reasons.

If any one is missing, there is no ADR. Easy to reverse → you'll just reverse it. Not surprising → nobody will wonder why. No real alternative → there's nothing to record beyond "we did the obvious thing."

What typically qualifies: architectural shape; integration patterns between modules or systems; technology choices carrying real lock-in (not every library — the ones that would take months to swap); ownership and boundary decisions, where the explicit *no*s matter as much as the *yes*es; deliberate deviations from the obvious path, which stop the next engineer from "fixing" something intentional; and constraints invisible in the code (compliance, a partner API's response-time contract).

### Plan decisions vs ADRs

A plan document's "Key Decisions" section already records why that plan looks the way it does, and it is archived together with the plan. Before promoting anything to an ADR, ask:

> Six months from now, could someone changing this area need to know why this choice was made?

If no, leave it in the plan document. Do not restate a plan decision as an ADR. The three tests above still apply — this one only separates plan-scoped decisions from ones that outlive the plan.
