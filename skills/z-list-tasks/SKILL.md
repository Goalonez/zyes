---
name: z-list-tasks
description: List the status, progress, and next step of all plan documents in the current project. Use only when the user explicitly asks to list or query plan status.
---

# List plans

Read-only summary of the current project's Zyes plan documents.

Resolve `<ZYES_PROJECT_ROOT>` from the repo's `<!-- zyes:start -->` block: resolve a relative `Root` against the repo root, or substitute `<ZYES_HOME>` from the global `<!-- zyes-global:start -->` block. Anchor it to the repo of the working directory (cwd) where the agent started; cross-repo paths are external code references, with the starting repo remaining the Zyes root. If the root cannot be resolved, state that the project's Zyes plans cannot be located and point the user to `z-init`.

## Collect

Collect every plan under `<ZYES_PROJECT_ROOT>/plans/active/`, covering both layouts:

- current layout: one directory per plan, so read `plans/active/*/PLAN.md`;
- legacy layout: a flat `plans/active/*.md` file. Read these in place and preserve their layout.

For each document parse:

- `status`, `created`, `slug` from frontmatter;
- the top-level heading as the title;
- the count of `- [x]` vs total items in "Implementation Milestones" for progress; for legacy plans, read "Execution Steps";
- the "next step" from the last line of the "Progress Log", or the default action for the status if absent.

When the user explicitly asks, also read `plans/done/` to show historical plans.

## Output

Output a compact table sorted by `created`:

| Status | Title | Progress | Next step | Path |
| --- | --- | --- | --- | --- |
| `in-progress` | … | 2/5 | next step from progress log | plans/active/2026-07-30-slug/PLAN.md |

Default next-step actions by status:

- `planning`: continue `z-brainstorm` to finish requirement confirmation and land the document.
- `ready`: use `z-implement` to start the first milestone.
- `in-progress`: use `z-implement` to continue the next unchecked milestone (prefer the next step from the progress log).
- `done` / `cancelled`: wrapped up; list only when viewing history.

When `plans/active/` is empty, simply state that the active plan list is empty. After the table, note only genuine anomalies that affect continuing work (e.g. a document missing frontmatter, or a status that contradicts its content). Report explicit document state and leave plan selection/execution to the user.
