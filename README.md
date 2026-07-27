<div align="center">

# Zyes

**A document-driven workflow for AI coding agents — plan in one Markdown file, execute across sessions and agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made for AI agents](https://img.shields.io/badge/for-AI%20coding%20agents-8A2BE2.svg)](#)

English | [简体中文](README.zh-CN.md)

</div>

---

Long tasks fall apart when the context window compacts, the session ends, or you switch to a different agent — the plan lives only in the chat, so the next agent starts from zero.

**Zyes fixes this by keeping the whole plan in a single local Markdown file.** Requirements, key decisions, execution steps, progress, and verification all live in one document that any agent can open and continue. No database, no state machine, no scripts — the document *is* the state.

```text
Confirm requirements → land one plan document → execute step by step, logging progress → wrap up when done
```

## Why Zyes

- **Document is the state** — a plan's frontmatter `status`, step checkboxes, and progress log express everything. Nothing hidden.
- **Pure Markdown, zero scripts** — every skill is plain-text instructions. No Python, no runtime, no lock-in to one agent's internals.
- **Cross-agent by design** — hand the plan document to any agent with one rule: *"read the plan, do the first unchecked step, check it off, append to the progress log."*
- **Stays out of your way** — for simple one-off tasks Zyes steps aside and lets the agent handle it directly. It only kicks in when you explicitly plan something worth persisting.

## Install

```bash
npx skills@latest add Goalonez/zyes
```

Follow the installer prompt to pick your coding agent and install all skills. No runtime dependencies.

## Skills at a glance

| Skill | Purpose |
| --- | --- |
| `/z-init` | Choose where plans are stored and wire up the project |
| `/z-brainstorm <need>` | Investigate the codebase, confirm requirements, land a plan document |
| `/z-implement` | Advance the next unchecked step, then wrap up when all are done |
| `/z-list-tasks` | List active plans with progress and next step |
| `/z-grilling` | Interrogate any decision, one question at a time (the proven core) |

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

`z-brainstorm` investigates the project, then confirms only the decisions that actually affect behavior, scope, and acceptance — facts it can find in the code, it won't ask you about. It lands one plan document: background & goals, key decisions, acceptance criteria, execution steps, progress log.

> If the project isn't initialized yet, Zyes **asks first** whether you want to set it up. Say no and it steps aside — no files created, your agent just handles the request normally.

### 3. Execute

```text
/z-implement execute this plan
```

`z-implement` advances **one** unchecked step at a time, then checks the box and appends a progress-log line (what changed, verification result, next step). When every step is done and acceptance is met, it wraps up: sets `status: done` and moves the file to `plans/done/`.

### 4. Pick up anywhere

```text
/z-list-tasks
```

Lists every active plan with its progress and next step — so a new session, or a different agent, can grab one and continue.

## The proven core: `z-grilling`

`z-grilling` is a battle-tested interrogation prompt (adapted from [mattpocock/skills](https://github.com/mattpocock/skills)). It walks the decision tree one question at a time, always offering a recommended answer, looking up facts itself instead of asking, and never acting until you've reached shared understanding.

`z-brainstorm` reuses it during planning, but you can invoke it standalone to pressure-test *any* idea:

```text
/z-grilling help me stress-test this architecture choice
```

## What a plan document looks like

```markdown
---
status: in-progress      # planning | ready | in-progress | done | cancelled
created: 2026-07-27
slug: settings-theme-toggle
---
# Add a theme toggle to the settings page

## Background & Goals
Users want a dark mode. Scope: settings page only. Out of scope: per-component theming.

## Key Decisions
- D1: Persist the choice in localStorage — no backend change needed for v1.

## Acceptance Criteria
- [x] AC1: Toggle switches the whole app between light/dark instantly.
- [ ] AC2: The choice survives a page reload.

## Execution Steps
- [x] 1. Add a theme context + toggle component.
- [ ] 2. Persist and rehydrate the choice from localStorage.

## Progress Log
- 2026-07-27 (session A): Finished step 1; verified toggle flips theme live. Next: persistence.
```

Checkboxes are the step state. The progress log is the handoff — any agent reads the bottom and knows exactly where to pick up.

## Where plans are stored

Pick one mode at init time:

| Mode | Location | Best for |
| --- | --- | --- |
| `shared` | `<repo>/.zyes` | Plans travel with the repo, shared by the team |
| `external` | `<ZYES_HOME>/<project-name>` | Plans kept in your personal space (e.g. an Obsidian vault), out of the repo |

Both use the same layout:

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/     # in-progress plans: YYYY-MM-DD-slug.md
│   └── done/       # completed / cancelled plans
└── knowledge/
    ├── CONTEXT.md  # reusable domain glossary (gets sharper the longer you use it)
    └── adr/        # load-bearing architecture decisions
```

Everything lives in readable, reviewable Markdown.

## When *not* to use Zyes

Zyes is for work that spans sessions or multiple steps and is worth persisting. For a quick one-off edit, a pure Q&A, or anything your agent can finish in one go — skip it. The skills are deliberately scoped to stay quiet in those cases.

## Credits

Zyes drew on:

- [mattpocock/skills](https://github.com/mattpocock/skills)
- [Trellis](https://github.com/mindfold-ai/Trellis)

## License

[MIT](LICENSE)
