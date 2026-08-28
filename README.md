<div align="center">

# Zyes

**A document-driven workflow for AI coding agents — the plan lives in Markdown.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made for AI agents](https://img.shields.io/badge/for-AI%20coding%20agents-8A2BE2.svg)](#)

English | [简体中文](README.zh-CN.md)

</div>

---

Long tasks fall apart when the context window compacts — the plan lives only in the chat, so when history gets summarized, the details are gone. Switching sessions or agents makes it worse, but compression is the real enemy.

**Zyes fixes this by keeping the whole plan in a single local Markdown file.** Requirements, key rules, implementation milestones, progress, and verification all live in one document that survives any compression. The document *is* the state.
```text
Confirm requirements → land one plan document → execute step by step, logging progress → wrap up when done
```

## Why Zyes

- **Document is the state** — a plan's frontmatter `status`, milestone checkboxes, acceptance checkboxes, and progress log express the task state.
- **Survives context compression** — the Markdown file remains the ground truth when chat history gets summarized.
- **Pure Markdown, zero scripts** — every skill is plain-text instructions, runtime-free and agent-neutral.
- **Works across sessions and agents** — hand the plan document to any agent with one rule: *"read the plan, do the first unchecked milestone, check it off, append to the progress log."*
- **Stays out of your way** — for simple one-off tasks Zyes steps aside and lets the agent handle it directly. It only kicks in when you explicitly plan something worth persisting.

## Install

```bash
npx skills@latest add Goalonez/zyes
```

Follow the installer prompt to pick your coding agent and install all skills. Installation adds Markdown skills only.

## Skills at a glance

| Skill | Purpose |
| --- | --- |
| `/z-init` | Choose where plans are stored and wire up the project |
| `/z-brainstorm <need>` | Investigate the codebase, confirm requirements, land a plan document |
| `/z-implement` | Advance the next unchecked milestone, then wrap up when all are done |
| `/z-list-tasks` | List active plans with progress and next step |
| `/z-grilling` | Interrogate decisions in dependency-aware rounds |
| `/z-domain` | Capture long-lived domain vocabulary and architecture decision records |

## Quick start

### 1. Initialize

```text
/z-init initialize this project
```

Pick a storage mode (`shared` or `external`); Zyes shows the full plan and waits for your confirmation before writing anything.

### 2. Plan

```text
/z-brainstorm add a theme toggle to the settings page
```

`z-brainstorm` investigates the project, looks up code-discoverable facts itself, then confirms the decisions that affect behavior, scope, and acceptance. It lands one requirement document: summary, requirement items, key rules, acceptance criteria, implementation milestones, progress log.

> If the project isn't initialized yet, Zyes **asks first** whether you want to set it up. Declining keeps the request in ordinary agent handling.

### 3. Execute

```text
/z-implement execute this plan
```

By default `z-implement` **runs through all remaining implementation milestones continuously**, checking the box and appending a progress-log line after each milestone. It pauses for ambiguity, plan conflicts, high-risk/irreversible operations, or failed verification (say "step mode" if you want per-milestone confirmation). Any non-code artifact it produces along the way (SQL scripts, review reports, manual checklists) lands in the plan's own `artifacts/` directory and gets indexed in the document. When every milestone is done and acceptance is met, it wraps up: sets `status: done` and moves the whole plan directory to `plans/done/`.

### 4. Pick up anywhere

```text
/z-list-tasks
```

Lists every active plan with its progress and next step — so a new session, or a different agent, can grab one and continue.

## The proven core: `z-grilling`

`z-grilling` is a battle-tested interrogation prompt (sourced from [mattpocock/skills](https://github.com/mattpocock/skills)). It maps decisions as a design tree, asks the current frontier in rounds, always offers a recommended answer, looks up facts itself, and waits for shared understanding before acting.

`z-brainstorm` reuses it during planning, but you can invoke it standalone to pressure-test *any* idea:

```text
/z-grilling help me stress-test this architecture choice
```

## What a plan document looks like

`plans/active/2026-07-27-settings-theme-toggle/PLAN.md`:

```markdown
---
status: in-progress      # planning | ready | in-progress | done | cancelled
created: 2026-07-27
slug: settings-theme-toggle
---
# Add a theme toggle to the settings page

## Requirement Summary
Users want a dark mode setting they can change directly from the settings page, and the choice should survive reloads.

## Requirement Items
- R1: Add a theme toggle to the settings page.
- R2: Apply the selected theme to the app immediately.
- R3: Preserve the selected theme across reloads.

## Key Rules
- K1: Persist the v1 choice in localStorage.

## Acceptance Criteria
- [x] AC1: Toggle switches the whole app between light/dark instantly.
- [ ] AC2: The choice survives a page reload.

## Implementation Milestones
- [x] 1. Add a theme context + toggle component.
- [ ] 2. Persist and rehydrate the choice from localStorage.

## Artifacts
- `artifacts/contrast-audit.md` — WCAG contrast check for the dark palette.

## Progress Log
- 2026-07-27 (session A): Completed milestone 1; verified toggle flips theme live. Next: persistence.
```

Checkboxes carry milestone and acceptance state. The progress log records milestone completion, verification, blockers, and confirmed requirement changes.

## Where plans are stored

Pick one mode at init time:

| Mode | Location | Best for |
| --- | --- | --- |
| `shared` | `<repo>/.zyes` | Plans travel with the repo, shared by the team |
| `external` | `<ZYES_HOME>/<project-name>` | Plans kept in your personal space (e.g. an Obsidian vault), out of the repo |

Both use the same layout, and `/z-init` creates the always-needed skeleton up front:

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/                  # one directory per in-progress plan
│   │   └── YYYY-MM-DD-slug/
│   │       ├── PLAN.md          # the plan document
│   │       └── artifacts/       # SQL, reports, checklists for this plan
│   └── done/                    # completed / cancelled plans
└── knowledge/                   # filled in by z-domain as work uncovers it
    └── CONTEXT.md               # domain glossary
```

**One plan is one directory.** Non-code artifacts produced while executing a plan — DDL scripts, execution-plan reports, manual verification checklists — stay in that plan's `artifacts/`. Wrapping up moves the whole directory to `plans/done/`, so links inside `PLAN.md` keep working.

**Plans are task-scoped; knowledge is long-lived.** `plans/` records the requirement, key rules, milestones, progress, and verification for one task. `knowledge/` holds the things future work has to respect: the project's shared vocabulary and load-bearing ADRs. Terms are written down the moment they're pinned down during interrogation; `knowledge/adr/` is created only when a decision qualifies. ADR-worthy decisions are hard to reverse, context-dependent for future readers, and the result of a real trade-off.

Everything lives in readable, reviewable Markdown.

## Credits

Zyes drew on:

- [mattpocock/skills](https://github.com/mattpocock/skills)
- [Trellis](https://github.com/mindfold-ai/Trellis)

## License

[MIT](LICENSE)
