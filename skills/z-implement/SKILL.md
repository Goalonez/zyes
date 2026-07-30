---
name: z-implement
description: Read an existing Zyes plan document, execute it step by step while logging progress, and wrap up when everything is done. Use only when the user explicitly asks to execute a plan. Not for cases with no plan document, or for scattered ad-hoc changes.
---

# Execute a plan

Advance the unfinished steps of a plan document in order (continuous by default, see section 3). Before executing, resolve the Zyes project root (read the repo's managed block). The Zyes root is always anchored to the repo of the working directory (cwd) where the agent started; even if the plan touches files in other repos (split front/back end, microservices, etc.), do not re-infer the repo root from that — treat cross-repo files only as referenced external code locations.

**Do not auto-initialize when no valid config is detected.** Ask the user whether to initialize Zyes; if they agree hand off to `z-init`, if they decline **stop this skill**, handle the request with the agent's own capabilities, and create no Zyes files.

## Output language

Match the language of the plan document being executed: write progress-log entries, appended notes, and any new headings in that document's language. When reporting to the user in chat, follow the language the user is conversing in.

## Getting the current date

Whenever you need today's date — for a progress-log entry, for example — **obtain it by actually running a command** (`date +%F` on macOS/Linux, `Get-Date -Format yyyy-MM-dd` in Windows PowerShell). Never infer it from your own memory, from a date that appears elsewhere in the conversation, or from dates already present in the plan document — in a long session the last logged date is usually stale, and copying it silently corrupts the log. Re-obtain the date before each write rather than reusing one from earlier in the session.

## 1. Choose a plan document

- Use the plan the user specified (by title or path).
- When unspecified, list plans under `<ZYES_PROJECT_ROOT>/plans/active/` whose `status` is `ready` or `in-progress` and let the user choose; if there's only one, confirm and start. Each plan is a directory containing `PLAN.md`; older plans may still be a flat `<date-slug>.md` file directly under `plans/active/` — read those in place and leave their layout as-is.
- Read the full text of the chosen document, plus relevant terms from `knowledge/CONTEXT.md` (if present), to keep wording consistent.

## 2. Execute the current step

1. On the first execution, change the document `status` from `ready` to `in-progress`.
2. In "Execution Steps", find the **first unchecked** (`- [ ]`) step as the current step.
3. Implement only that one step. When you hit ambiguity, a conflict with the plan, or scope creep, **stop** and clarify with the user — don't expand on your own.
4. Only touch product code, tests, config, and docs covered by the approved plan; write plan and domain documents under `<ZYES_PROJECT_ROOT>`, and non-code artifacts into the current plan's `artifacts/` (see "Where non-code artifacts go" below).
5. Implement following the "Execution guidelines" below, and use judgment to choose the smallest relevant verification that provides sufficient evidence for the current step and its acceptance criteria.

## Where non-code artifacts go

Execution often produces files that are **not part of the product build**: DDL/SQL scripts, execution-plan and index review reports, manual verification checklists, data reconciliation results, performance measurements, migration runbooks. All of these go into the current plan's own directory:

```text
<ZYES_PROJECT_ROOT>/plans/active/<date-slug>/artifacts/<name>.md
```

Create `artifacts/` lazily, on first use. For a legacy flat plan file (`plans/active/<date-slug>.md`), create the sibling directory `plans/active/<date-slug>/artifacts/` and use that.

Deciding where a file belongs:

- Consumed by the product build, release process, or version control (Flyway/Liquibase migration scripts, real config, official documentation) → put it in the code repository following that repo's existing conventions.
- Only meant to be read by a human, executed once by hand, or kept for audit → `artifacts/`.
- When unsure, choose `artifacts/` and say so when you report.

**Do not create analysis reports, SQL drafts, acceptance checklists, benchmark output, or similar scratch files inside the code repository.** Delete throwaway verification scripts once used, keeping only the conclusion and any output worth retaining in `artifacts/`. Name artifacts in short kebab-case without a date prefix (the plan directory name already carries the date). When an artifact evolves, **update it in place** — do not create a second near-identical file alongside it.

Every time you write or meaningfully revise an artifact, register it in the plan document's "Artifacts" section as a relative link plus a one-line description of what it is and what it's for. Relative links stay valid after wrap-up because the whole plan directory moves together. If a plan document predates this section, add it above "Progress Log", using the document's own language.

## Execution guidelines

Code implementation must follow the principle of minimal implementation: prioritize reusing existing code and the project's existing style, solve only the explicitly requested requirement, do not proactively expand functionality, introduce unnecessary abstractions, or over-engineer, and avoid splitting logic into multiple methods when it can be clearly implemented within a single function or method.

## 3. Log progress

After completing the step, in the document:

- Check the corresponding step as `- [x]`.
- Check any satisfied acceptance criteria as `- [x]`.
- Register any artifact written or revised during this step in "Artifacts" (see "Where non-code artifacts go").
- Append one line to "Progress Log": `YYYY-MM-DD (session/agent): what was done; the verification actually run and its result; recommended next step`. Note the reason for any verification not run. Obtain the date by running a command as described in "Getting the current date" — do not copy the date from the previous log line.

The progress log is the cross-session/cross-agent handoff: any new session can pick up by reading the bottom of the document.

**Continuous by default**: for plans with `status` `ready` or `in-progress`, decisions already converged in the brainstorm stage, so execution **advances through all remaining steps continuously** — checking the box and appending a progress-log line after each step, but **not stopping for per-step confirmation**. Only stop to clarify with the user when:

- a step is ambiguous, conflicts with the plan, or requires expanding scope;
- a high-risk / irreversible operation touching a safety boundary is needed (deleting files, dependency changes, dangerous Git, database writes, real external side effects, etc.);
- verification fails and can't be automatically diagnosed and fixed.

**Step mode**: when the user says "step by step / single step / step", switch to reporting after each completed step and waiting for confirmation before continuing.

## 4. Wrap up (when everything is done)

When **all execution steps are `[x]` and all acceptance criteria are satisfied**, this skill wraps up naturally — no separate wrap-up entry point needed:

1. Report to the user: all steps done, acceptance met, about to wrap up.
2. After the user confirms, change `status` to `done` and move **the whole plan directory** — `PLAN.md` together with `artifacts/` — from `plans/active/` to `plans/done/`. Move the directory as a unit so the relative links inside `PLAN.md` keep resolving; never move `PLAN.md` on its own and leave its artifacts behind.
3. If execution surfaced stable domain terms or load-bearing decisions, update `knowledge/` (rules in z-brainstorm section 3).

**Cancel**: when the user explicitly abandons this plan, change `status` to `cancelled`, append the reason to the progress log, move the whole plan directory to `plans/done/`, and keep existing content for traceability.

Do not auto-commit or push Git; wrap-up only changes the document's status and location.
