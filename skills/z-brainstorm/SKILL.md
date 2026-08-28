---
name: z-brainstorm
description: Investigate the codebase, confirm requirements, and land one multi-step piece of work into a plan document when the user explicitly asks to plan persistent work.
---

# Plan a requirement

Turn a user request into a confirmed plan document. During planning you may investigate the repo and maintain domain vocabulary while keeping product code unchanged.

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

## 2. Land the plan document

Once decisions converge, show the user a concise requirement-document summary (summary, requirement items, key rules, acceptance criteria, implementation milestones), recommend a path, and ask whether to land it. After the user confirms, create one directory for the plan and write the plan document inside it:

```text
<ZYES_PROJECT_ROOT>/plans/active/YYYY-MM-DD-<slug>/PLAN.md
```

`slug` is the title normalized to lowercase kebab-case; the date is today's, obtained as described in "Getting the current date" above. At planning time, create only `PLAN.md`; `z-implement` adds `artifacts/` and the "Artifacts" section when it registers the first artifact. If a directory of the same name already exists, let the user choose to continue that plan or pick another name. Use the fixed structure below (translate the headings into the output language):

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

Split implementation milestones into independently verifiable key nodes needed to satisfy the acceptance criteria. Prefer reusing existing code and project conventions discovered during investigation. Keep the plan inside confirmed scope: required functionality, necessary verification, and directly relevant docs. When the plan is landed before execution starts, set `status` to `ready`; while still interrogating with decisions unsettled, use `planning`.

## 3. Long-lived domain knowledge

Terms and load-bearing decisions are owned by [z-domain](../z-domain/SKILL.md) — terms are recorded inline during interrogation (section 1), and a decision is promoted to an ADR only when it constrains future work beyond this plan. Everything specific to this plan stays in "Key Rules" above.

## Report

After landing the document, report the plan directory's absolute path and `status`, and note that `z-implement` can start execution. If a substantive scope change appears after implementation begins, create a new plan directory and preserve the executing or completed plan as history.
