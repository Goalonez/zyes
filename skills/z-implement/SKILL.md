---
name: z-implement
description: Read an existing Zyes plan document, execute it milestone by milestone while logging progress, and wrap up when everything is done.
---

# Execute a plan

Advance the unfinished implementation milestones of a plan document in order (continuous by default, see section 3). Resolve `<ZYES_PROJECT_ROOT>` from the repo's `<!-- zyes:start -->` block: resolve a relative `Root` against the repo root, or substitute `<ZYES_HOME>` from the global `<!-- zyes-global:start -->` block. Anchor it to the repo of the working directory (cwd) where the agent started; cross-repo paths are external code references, with the starting repo remaining the Zyes root.

**If the project root cannot be resolved**, ask the user whether to initialize Zyes; if they agree hand off to `z-init`, otherwise return to ordinary agent handling.

## Output language

Match the language of the plan document being executed: write progress-log entries, appended notes, and any new headings in that document's language. When reporting to the user in chat, follow the language the user is conversing in.

## Getting the current date

Whenever you need today's date — for a progress-log entry, for example — **obtain it by actually running a command** (`date +%F` on macOS/Linux, `Get-Date -Format yyyy-MM-dd` in Windows PowerShell). Use command output as the source of truth because conversation dates and prior log dates are often stale. Re-obtain the date before each write.

## 1. Choose a plan document

- Use the plan the user specified (by title or path).
- When unspecified, list plans under `<ZYES_PROJECT_ROOT>/plans/active/` whose `status` is `ready` or `in-progress` and let the user choose; if there's only one, confirm and start. Each plan is a directory containing `PLAN.md`; older plans may still be a flat `<date-slug>.md` file directly under `plans/active/` — read those in place and leave their layout as-is.
- Read the full text of the chosen document, plus relevant terms from `knowledge/CONTEXT.md` (if present) and the ADRs relevant to the area you're touching, to keep wording consistent.

## 2. Execute the current milestone

1. On the first execution, change the document `status` from `ready` to `in-progress`.
2. In "Implementation Milestones" (or legacy "Execution Steps"), find the **first unchecked** (`- [ ]`) milestone as the current milestone.
3. Implement only that one milestone. When you hit ambiguity, a conflict with the plan, or scope creep, **stop** and clarify with the user.
4. Only touch product code, tests, config, and docs covered by the approved plan; write plan and domain documents under `<ZYES_PROJECT_ROOT>`, and non-code artifacts into the current plan's `artifacts/` (see "Where non-code artifacts go" below).
5. Implement following the "Execution guidelines" below, and use judgment to choose the smallest relevant verification that provides sufficient evidence for the current milestone and its acceptance criteria.

## Where non-code artifacts go

Execution often produces plan-side artifacts: DDL/SQL scripts, execution-plan and index review reports, manual verification checklists, data reconciliation results, performance measurements, migration runbooks. All of these go into the current plan's own directory:

```text
<ZYES_PROJECT_ROOT>/plans/active/<date-slug>/artifacts/<name>
```

Create `artifacts/` lazily, on first use. For a legacy flat plan file (`plans/active/<date-slug>.md`), create the sibling directory `plans/active/<date-slug>/artifacts/` and use that.

Deciding where a file belongs:

- Consumed by the product build, release process, or version control (Flyway/Liquibase migration scripts, real config, official documentation) → put it in the code repository following that repo's existing conventions.
- Only meant to be read by a human, executed once by hand, or kept for audit → `artifacts/`.
- When unsure, choose `artifacts/` and say so when you report.

Choose the artifact type before writing:

- `*.sql`: executable SQL only, with minimal comments and placeholders.
- `*-checklist.md`: manual verification checklist.
- `*-runbook.md`: operational steps.
- `*-report.md`: analysis or audit result.
- `*.md`: fallback for artifacts outside the typed suffixes above.

For SQL artifacts, put the copyable SQL first. Explanations, placeholder notes, and manual cautions go after the SQL, or into a separate `*-runbook.md` when they become long.

Keep analysis reports, SQL drafts, acceptance checklists, benchmark output, and similar plan artifacts in `artifacts/`. Delete throwaway verification scripts once used, keeping only the conclusion and any output worth retaining in `artifacts/`. Name artifacts in short kebab-case; the plan directory already carries the date. When an artifact evolves, **update it in place**.

Every time you write or meaningfully revise an artifact, register it in the plan document's "Artifacts" section as a relative link plus a one-line description of its type and purpose. Relative links stay valid after wrap-up because the whole plan directory moves together. If the plan document lacks an "Artifacts" section, add it above "Progress Log", using the document's own language.

## Execution guidelines

Code implementation must follow the principle of minimal implementation: prioritize reusing existing code and the project's existing style, solve the explicitly requested requirement, keep the scope tight, and keep logic in a single function or method when that remains clear.

## 3. Log progress

After completing an implementation milestone, in the document:

- Check the corresponding milestone as `- [x]`.
- Check any satisfied acceptance criteria as `- [x]`.
- Register any artifact written or revised during this milestone in "Artifacts" (see "Where non-code artifacts go").
- Append one line to "Progress Log": `YYYY-MM-DD (session/agent): completed milestone; verification actually run and result; recommended next milestone`. If the section still contains only a `pending` placeholder (or legacy `none`), replace it with the first real log line. Note the reason for any skipped verification. Obtain the date by running a command as described in "Getting the current date".

The progress log is a compact task history. Write one line when a milestone completes, a blocker appears, or the user confirms a requirement change.

**Continuous by default**: for plans with `status` `ready` or `in-progress`, decisions already converged in the brainstorm stage, so execution **advances through all remaining milestones continuously** — checking the box and appending a progress-log line after each milestone. Stop to clarify with the user when:

- a milestone is ambiguous, conflicts with the plan, or requires expanding scope;
- a high-risk / irreversible operation touching a safety boundary is needed (deleting files, dependency changes, dangerous Git, database writes, real external side effects, etc.);
- verification fails and needs a user decision after diagnosis attempts.

**Step mode**: when the user says "step by step / single step / step", switch to reporting after each completed milestone and waiting for confirmation before continuing.

## 4. Wrap up (when everything is done)

When **all implementation milestones are `[x]` and all acceptance criteria are satisfied**, this skill wraps up naturally:

1. Report to the user: all milestones done, acceptance met, about to wrap up.
2. After the user confirms, change `status` to `done` and move **the whole plan directory** — `PLAN.md` together with `artifacts/` — from `plans/active/` to `plans/done/`. Move the directory as a unit so the relative links inside `PLAN.md` keep resolving.
3. If execution pinned down or overturned a domain term, or forced a decision that constrains future work beyond this plan, hand off to [z-domain](../z-domain/SKILL.md). Apply the ADR/glossary bar from that skill.

**Cancel**: when the user explicitly abandons this plan, change `status` to `cancelled`, append the reason to the progress log, move the whole plan directory to `plans/done/`, and keep existing content for traceability.

Wrap-up changes the document's status and location. Git commits and pushes remain explicit user actions.
