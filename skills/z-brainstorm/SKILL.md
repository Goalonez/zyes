---
name: z-brainstorm
description: Investigate the codebase, confirm requirements, and land one multi-step piece of work into a plan document. Use only when the user explicitly asks to plan. Not for simple one-off tasks, pure Q&A, or changes the agent can just do directly.
---

# Plan a requirement

Turn a user request into a confirmed plan document. During planning you may investigate the repo and maintain domain vocabulary, but you do not modify product code.

Resolve `<ZYES_PROJECT_ROOT>` from the repo's `<!-- zyes:start -->` block: resolve a relative `Root` against the repo root, or substitute `<ZYES_HOME>` from the global `<!-- zyes-global:start -->` block. Anchor it to the repo of the working directory (cwd) where the agent started; files in other repos do not change the Zyes root.

**If the project root cannot be resolved**, ask the user in one line: initialize Zyes to persist this plan?

- User agrees → hand off to `z-init`, then return to this skill.
- User declines or just wants a quick fix → **stop this skill**, create no Zyes files, and handle the request with the agent's own capabilities.

Plan documents are saved under `<ZYES_PROJECT_ROOT>/plans/active/`, one directory per plan.

## Getting the current date

Whenever you need today's date — for a plan directory name or the `created` field — **obtain it by actually running a command** (`date +%F` on macOS/Linux, `Get-Date -Format yyyy-MM-dd` in Windows PowerShell). Never infer it from your own memory, from a date that appears elsewhere in the conversation, or from dates found in existing documents — those are routinely wrong or stale. If you cannot run a command, ask the user for today's date instead of guessing.

## Output language

Write the plan document — including section headings, decisions, acceptance criteria, and progress log — in the **same language the user is conversing in**. If the repo's existing docs/plans are clearly in another language, match those instead. The section headings in the template below are **labels to translate into the output language, not literal strings to copy verbatim**. Keep the frontmatter keys (`status`, `created`, `slug`) and their enum values in English; translate only human-readable prose.

## 1. Investigate and interrogate

1. Read the code, tests, config, and project docs relevant to the request.
2. Read `<ZYES_PROJECT_ROOT>/knowledge/CONTEXT.md` (if present) and the ADRs relevant to the area you're touching, and reuse the domain vocabulary already defined.
3. When there are **substantive decisions** that need the user's call, apply the rules from [z-grilling](../z-grilling/SKILL.md): ask one question at a time, look up facts you can find yourself, offer a recommended answer for each question, and don't land anything until you've reached shared understanding. Don't manufacture questions when there is no substantive decision.

While interrogating, whenever a domain term gets pinned down, an existing term turns out to be overloaded, or the user's wording contradicts the glossary, hand off to [z-domain](../z-domain/SKILL.md) and record it **right then** — not after the plan lands. That is the moment the wording and the reason are both still in hand.

## 2. Land the plan document

Once decisions converge, show the user a plan summary (background, scope, key decisions, acceptance criteria, execution steps), recommend a path, and ask whether to land it. After the user confirms, create one directory for the plan and write the plan document inside it:

```text
<ZYES_PROJECT_ROOT>/plans/active/YYYY-MM-DD-<slug>/PLAN.md
```

`slug` is the title normalized to lowercase kebab-case; the date is today's, obtained as described in "Getting the current date" above. Do not create `artifacts/` now — `z-implement` creates it on demand. If a directory of the same name already exists, let the user choose to continue that plan or pick another name — do not overwrite. Use the fixed structure below (translate the headings into the output language); write `none` for sections with no content:

```markdown
---
status: ready          # planning | ready | in-progress | done | cancelled
created: YYYY-MM-DD
slug: <slug>
---
# <Title>

## Background & Goals
Problem, goals, in scope, out of scope.

## Key Decisions
- D1: <decision> — rationale (from interrogation)

## Acceptance Criteria
- [ ] AC1: <observable outcome>

## Execution Steps
- [ ] 1. <independently verifiable vertical slice>
- [ ] 2. ...

## Artifacts
- (registered by z-implement as artifacts are produced: `artifacts/<name>.md` — what it is and what it's for)

## Progress Log
- (appended by z-implement during execution: date (session/agent): what was done; verification result; next step)
```

Split execution steps into the smallest independently verifiable vertical slices needed to satisfy the acceptance criteria; don't pad with trivial steps. Prefer reusing existing code and project conventions discovered during investigation. Do not plan speculative functionality, unrelated refactors, unnecessary abstractions, or work outside the confirmed scope. When the plan is just landed and not yet started, set `status` to `ready`; while still interrogating with decisions unsettled, use `planning`.

## 3. Long-lived domain knowledge

Terms and load-bearing decisions are owned by [z-domain](../z-domain/SKILL.md) — terms are recorded inline during interrogation (section 1), and a decision is promoted to an ADR only when it constrains future work beyond this plan. Everything specific to this plan stays in "Key Decisions" above.

## Handoff

After landing the document, report the plan directory's absolute path and `status`, and note that `z-implement` can start execution. If a substantive scope change appears after implementation begins, create a new plan directory — do not rewrite a plan that's already executing or done.
