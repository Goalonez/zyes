---
name: z-brainstorm
description: Investigate the codebase, confirm requirements, and land one multi-step piece of work into a plan document. Use only when the user explicitly asks to plan. Not for simple one-off tasks, pure Q&A, or changes the agent can just do directly.
---

# Plan a requirement

Turn a user request into a confirmed plan document. During planning you may investigate the repo and maintain domain vocabulary, but you do not modify product code.

First resolve the Zyes project root: read the `<!-- zyes:start -->` managed block in the repo's `AGENTS.md`/`CLAUDE.md`. The Zyes root is always anchored to the repo of the working directory (cwd) where the agent started; even if the requirement touches files in other repos (split front/back end, microservices, etc.), do not re-infer the repo root from that — treat cross-repo files only as referenced external code locations.

**Do not auto-initialize when no valid config is detected.** Ask the user in one line: initialize Zyes to persist this plan?

- User agrees → hand off to `z-init`, then return to this skill.
- User declines or just wants a quick fix → **stop this skill**, create no Zyes files, and handle the request with the agent's own capabilities.

Plan documents are saved under `<ZYES_PROJECT_ROOT>/plans/active/`.

## Output language

Write the plan document — including section headings, decisions, acceptance criteria, and progress log — in the **same language the user is conversing in**. If the repo's existing docs/plans are clearly in another language, match those instead. The section headings in the template below are **labels to translate into the output language, not literal strings to copy verbatim**. Keep the frontmatter keys (`status`, `created`, `slug`) and their enum values in English; translate only human-readable prose.

## 1. Investigate and interrogate

1. Read the code, tests, config, and project docs relevant to the request.
2. Read `<ZYES_PROJECT_ROOT>/knowledge/CONTEXT.md` (if present) and relevant ADRs, and reuse the domain vocabulary already defined.
3. When there are **substantive decisions** that need the user's call, apply the rules from [z-grilling](../z-grilling/SKILL.md): ask one question at a time, look up facts you can find yourself, offer a recommended answer for each question, and don't land anything until you've reached shared understanding. Don't manufacture questions when there is no substantive decision.

## 2. Land the plan document

Once decisions converge, show the user a plan summary (background, scope, key decisions, acceptance criteria, execution steps), recommend a path, and ask whether to land it. After the user confirms, write a single file:

```text
<ZYES_PROJECT_ROOT>/plans/active/YYYY-MM-DD-<slug>.md
```

`slug` is the title normalized to lowercase kebab-case; use the current local date. If a file of the same name already exists, let the user choose to continue that file or pick another name — do not overwrite. Use the fixed structure below (translate the headings into the output language); write `none` for sections with no content:

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

## Progress Log
- (appended by z-implement during execution: date (session/agent): what was done; verification result; next step)
```

Split execution steps into independently verifiable vertical slices; don't pad with trivial steps. When the plan is just landed and not yet started, set `status` to `ready`; while still interrogating with decisions unsettled, use `planning`.

## 3. Maintain domain knowledge (as needed)

When planning surfaces stable new business terms, conflicts with the existing glossary, or produces a load-bearing architecture decision that's hard to reverse:

- Write terms into `<ZYES_PROJECT_ROOT>/knowledge/CONTEXT.md` (record only stable business vocabulary, meaning, and boundaries — not implementation details or task scope).
- Write hard-to-reverse load-bearing decisions with real alternatives into `knowledge/adr/NNNN-<slug>.md`, capturing Context / Decision / Alternatives / Consequences. Don't create an ADR for ordinary implementation trade-offs.
- Create files and directories lazily as needed; skip silently when there's no content.

## Handoff

After landing the document, report the file's absolute path and `status`, and note that `z-implement` can start execution. If a substantive scope change appears after implementation begins, create a new plan document — do not rewrite a plan that's already executing or done.
