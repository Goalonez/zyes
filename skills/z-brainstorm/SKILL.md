---
name: z-brainstorm
description: Investigate the codebase, confirm requirements, and create or revise an executable plan document when the user explicitly plans persistent work or revisits the requirements of an existing Zyes task.
---

# Plan a requirement

Turn a user request into a confirmed, executable plan document. During planning you may investigate the repo and maintain domain vocabulary while keeping product code unchanged.

For the same unfinished task, use the user's specified plan or the current plan and read it before investigating. Clarifications, solution changes, and scope adjustments default to revising that plan after confirmation. Split unfinished work into a new plan only for an independent goal or when the user explicitly asks to split it; judge by the task goal, not discussion length or change size.

Resolve `<ZYES_PROJECT_ROOT>` from the repo's `<!-- zyes:start -->` block: resolve a relative `Root` against the repo root, or substitute `<ZYES_HOME>` from the global `<!-- zyes-global:start -->` block. Anchor it to the repo of the working directory (cwd) where the agent started; cross-repo paths are external code references, with the starting repo remaining the Zyes root.

**If the project root cannot be resolved**, ask the user in one line: initialize Zyes to persist this plan?

- User agrees → hand off to `z-init`, then return to this skill.
- User declines or just wants a quick fix → **stop this skill** and handle the request with the agent's own capabilities.

Plan documents are saved under `<ZYES_PROJECT_ROOT>/plans/active/`, one directory per plan.

## Getting the current date

Whenever you need today's date — for a plan directory name or the `created` field — **obtain it by actually running a command** (`date +%F` on macOS/Linux, `Get-Date -Format yyyy-MM-dd` in Windows PowerShell). Use command output as the source of truth because conversation and document dates are often stale. If command execution is unavailable, ask the user for today's date.

## Output language

Write the plan document — including section headings, decisions, acceptance criteria, and progress log — in the **same language the user is conversing in**. If the repo's existing docs/plans are clearly in another language, match those instead. Translate the section-heading labels in the template below into the output language. Keep the frontmatter keys (`status`, `created`, `slug`) and their enum values in English; translate only human-readable prose.

## 1. Investigate and interrogate

1. Read the code, tests, config, and project docs relevant to the request.
2. Read `<ZYES_PROJECT_ROOT>/knowledge/CONTEXT.md` (if present) and the ADRs relevant to the area you're touching, and reuse the domain vocabulary already defined.
3. When there are **substantive decisions** that need the user's call, apply the rules from [z-grilling](../z-grilling/SKILL.md): map decisions as a dependency tree, ask the current frontier in rounds, look up facts you can find yourself, offer a recommended answer for each question, and land the document after shared understanding. Ask only questions that affect behavior, scope, acceptance, or risk.

While interrogating, whenever a domain term gets pinned down, an existing term turns out to be overloaded, or the user's wording contradicts the glossary, hand off to [z-domain](../z-domain/SKILL.md) and record it immediately. That is the moment the wording and the reason are both still in hand.

## 2. Land or revise the plan document

Once decisions converge, show a concise summary of the requirements or changes and ask for confirmation. For an existing plan, update the affected requirements, key rules, acceptance criteria, and milestones in place, preserve its identity and any `in-progress` status, and append one progress-log line with the change and reason. Preserve valid completed items; uncheck items invalidated by the change and add any necessary rework. Keep only what execution and resumption need.

For a new plan, after confirmation create one directory and write the plan document inside it:

```text
<ZYES_PROJECT_ROOT>/plans/active/YYYY-MM-DD-<slug>/PLAN.md
```

`slug` is the title normalized to lowercase kebab-case; the date is today's, obtained as described in "Getting the current date" above. For a new plan, create only `PLAN.md`; `z-implement` adds `artifacts/` and the "Artifacts" section only when an independent attachment is needed. If a directory of the same name already exists, let the user choose to continue that plan or pick another name. Use the fixed structure below (translate the headings into the output language):

```markdown
---
status: ready          # planning | ready | in-progress | done | cancelled
created: YYYY-MM-DD
slug: <slug>
---
# <Title>

## Requirement Summary
1-3 sentences: the problem, why it matters now, and the desired result.

## Requirement Items
- R1: <positive requirement statement>

## Key Rules
- K1: <confirmed rule or constraint that affects implementation>

## Acceptance Criteria
- [ ] AC1: <observable outcome>

## Implementation Milestones
- [ ] 1. <key milestone, independently verifiable when complete>
- [ ] 2. ...

## Progress Log
- pending
```

Write requirements as positive statements. Reserve negative boundaries for likely mistakes, explicit user rejections, and safety limits. Keep "Key Rules" to confirmed rules that steer execution.

Split implementation milestones into independently verifiable key nodes needed to satisfy the acceptance criteria. Prefer reusing existing code and project conventions discovered during investigation. Keep the plan inside confirmed scope: required functionality, necessary verification, and directly relevant docs. For plans that have not started execution, set `status` to `ready` after confirmation; use `planning` while initial decisions remain unsettled.

## 3. Long-lived domain knowledge

Terms and load-bearing decisions are owned by [z-domain](../z-domain/SKILL.md) — terms are recorded inline during interrogation (section 1), and a decision is promoted to an ADR only when it constrains future work beyond this plan. Everything specific to this plan stays in "Key Rules" above.

## Report

After creating or revising the document, report its absolute path and `status`, and note that `z-implement` can start or continue execution.
