---
name: z-list-tasks
description: List the status, progress, and next step of all plan documents in the current project. Use only when the user explicitly asks to list or query plan status.
---

# List plans

Read-only summary of the current project's Zyes plan documents. Do not create, modify, or start executing any plan.

First resolve the Zyes project root (read the repo's managed block), anchored to the repo of the working directory (cwd) where the agent started — do not change the root based on other repo files the user mentions. **When no valid config is detected**, reply directly that Zyes is not enabled for this project (no plan documents), and do not ask whether to initialize or initialize on the user's behalf — the user will run `z-init` explicitly when needed.

## Collect

Read all `*.md` files under `<ZYES_PROJECT_ROOT>/plans/active/`. For each document parse:

- `status`, `created`, `slug` from frontmatter;
- the top-level heading as the title;
- the count of `- [x]` vs total items in "Execution Steps" for progress;
- the "next step" from the last line of the "Progress Log", or the default action for the status if absent.

When the user explicitly asks, also read `plans/done/` to show historical plans.

## Output

Output a compact table sorted by `created`:

| Status | Title | Progress | Next step | Path |
| --- | --- | --- | --- | --- |
| `in-progress` | … | 2/5 | next step from progress log | plans/active/… |

Default next-step actions by status:

- `planning`: continue `z-brainstorm` to finish requirement confirmation and land the document.
- `ready`: use `z-implement` to start the first step.
- `in-progress`: use `z-implement` to continue the next unchecked step (prefer the next step from the progress log).
- `done` / `cancelled`: wrapped up; list only when viewing history.

When `plans/active/` is empty, simply state that there are no active plans. After the table, note only genuine anomalies that affect continuing work (e.g. a document missing frontmatter, or a status that contradicts its content). Do not infer missing fields, and do not automatically select or start any plan.
