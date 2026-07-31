---
name: z-init
description: Initialize the Zyes workflow storage location for the current repo. Use only when the user explicitly asks, or when another Zyes skill is missing a valid config and needs initialization.
---

# Set up Zyes

Determine a single Zyes project root for the current repo, write a locator managed block into the project description file, and scaffold the storage directory structure. This skill configures the storage location and creates the empty directory skeleton plus a `CONTEXT.md` starter — it does not create any plan documents. Show the full draft and get explicit confirmation from the user before writing anything; when updating an existing file, touch only the managed block and preserve all other content.

## Directory layout

The same layout applies in both modes. The init step creates this full skeleton up front — the two `plans/` subdirectories, `knowledge/adr/`, and a `CONTEXT.md` starter — so the workspace is ready to use immediately:

```text
<ZYES_PROJECT_ROOT>/
├── plans/
│   ├── active/                      # in-progress plans, one directory per plan
│   │   └── YYYY-MM-DD-<slug>/       # created by z-brainstorm
│   │       ├── PLAN.md              # the plan document itself
│   │       └── artifacts/           # non-code artifacts for this plan (lazily created)
│   └── done/                        # completed / cancelled plans (whole directories)
└── knowledge/                       # filled in by z-domain, empty until then
    ├── CONTEXT.md                   # project glossary (created as a starter skeleton)
    └── adr/                         # load-bearing decisions: NNNN-slug.md
```

**One plan is one directory.** The plan document is always named `PLAN.md`, and every non-code artifact produced while executing that plan lives in its sibling `artifacts/`. This keeps each plan self-contained, so wrapping up moves one directory and the relative links inside `PLAN.md` stay valid. This skill creates only `plans/active/`, `plans/done/`, and `knowledge/adr/` — individual plan directories and their `artifacts/` are created later, on demand.

The `knowledge/` scaffold is created empty on purpose, so the workspace shows from day one where domain knowledge belongs. [z-domain](../z-domain/SKILL.md) owns its contents and treats the starter as a placeholder to replace, never as existing content.

## Anchoring rule

The Zyes root is **always anchored to the repo of the working directory (cwd) where the agent started**. Even when the user mentions or asks you to read/write files that belong to **another repo** (split front/back end, multi-repo microservices, etc.), **do not** re-infer the repo root from those file paths and do not look for a managed block in that other repo. Cross-repo files are only "referenced external code locations" and do not change the Zyes root. All Zyes skills follow this rule when resolving the root.

## 1. Explore

Find the repo root by walking up from the current directory (see anchoring rule above). To locate the root, only check for repo markers such as `.git`; do not read directory contents beyond what this needs. Then read only the specific files this skill requires:

- `AGENTS.md` and `CLAUDE.md` at the repo root;
- any existing `<!-- zyes:start -->` managed block in those files;
- the Zyes home managed block in the global `AGENTS.md` or `CLAUDE.md` available to the current session.

Keep reads narrowly scoped to the paths above. This skill only needs the description files and their managed blocks, so target those exact paths directly (e.g. read `AGENTS.md` / `CLAUDE.md` by name) instead of listing or scanning the whole repo. During initialization you **must not** read unrelated or non-essential artifacts — this explicitly includes `.env` and other environment/secret/credential files, and extends to source code, dependency directories, build output, and anything else not listed above.

Choose the project description file in this order: use `AGENTS.md` if it exists; otherwise use an existing `CLAUDE.md`; if neither exists, ask the user which to create and recommend `AGENTS.md`.

## 2. Choose a mode

When a valid managed block already exists, prefer keeping the current mode and ask whether to reconfigure. Otherwise let the user choose:

- `shared`: always uses `<repo>/.zyes`, so the workspace sits alongside the codebase and is reachable by anyone working in the repo.
- `external`: uses `<ZYES_HOME>/<project-name>` (e.g. a personal Obsidian vault); the repo managed block does not record a personal absolute path.

For external mode, read the Zyes home root from the corresponding global description file's managed block; if absent, ask for the absolute path and write it into the global description file. The project name defaults to the repo directory name normalized to lowercase kebab-case. When the target directory already exists but cannot be confirmed as belonging to the current repo, show the conflict and let the user choose to reuse or rename — do not overwrite.

## 3. Show and confirm

Show in one go: the mode, the final absolute project root, the directory skeleton to be created (the `plans/active`, `plans/done`, `knowledge/adr` directories and the `CONTEXT.md` starter), the project managed block to be written, and (for external mode) the global Zyes home managed block. Then ask the user to confirm writing the config and scaffolding the workspace, and invite them to describe any changes instead — phrase this in the language the user is conversing in. Do not proceed without an explicit confirmation. If the external path is outside the writable scope, request runtime authorization separately.

## 4. Write and verify

- Create the directory skeleton under the project root: `plans/active/`, `plans/done/`, `knowledge/adr/`, and a `knowledge/CONTEXT.md` starter (see the template below). If any of these already exist, keep them as-is and never overwrite existing content.
- Add or update the managed block in place; never append a duplicate block. For external mode, also update the global Zyes home managed block.
- Re-read all written files to confirm correctness.
- Report the mode, project root, the created directories and `CONTEXT.md`, and the modified description files. For external mode, remind the user to open a new session to load the global config. If there's a pending requirement, ask whether to proceed to `z-brainstorm`.

## Managed block templates

### Shared

```markdown
<!-- zyes:start -->
## Zyes workflow

- Mode: `shared`
- Root: `.zyes`

Use Zyes skills for work worth persisting across sessions. Plan documents are saved as `.zyes/plans/active/<date-slug>/PLAN.md`; non-code artifacts produced for a plan (SQL scripts, review reports, manual checklists) go in that plan's `artifacts/` directory, not into the codebase. Before work that touches this project's domain, read the glossary `.zyes/knowledge/CONTEXT.md` and any ADRs under `.zyes/knowledge/adr/` relevant to the area you're touching, and reuse the vocabulary defined there.
Only use this section when the current agent has Zyes skills installed and callable; otherwise ignore it and follow the project's existing workflow.
<!-- zyes:end -->
```

### External

```markdown
<!-- zyes:start -->
## Zyes workflow

- Mode: `external`
- Project: `project-name`

Read the Zyes home from the user's global `AGENTS.md` (or `CLAUDE.md`); the project workflow root is `<ZYES_HOME>/project-name`. Plan documents are saved as `<root>/plans/active/<date-slug>/PLAN.md`; non-code artifacts produced for a plan (SQL scripts, review reports, manual checklists) go in that plan's `artifacts/` directory, not into the codebase. Before work that touches this project's domain, read the glossary `<root>/knowledge/CONTEXT.md` and any ADRs under `<root>/knowledge/adr/` relevant to the area you're touching, and reuse the vocabulary defined there.
Only use this section when the current agent has Zyes skills installed and callable and can resolve the personal Zyes home; otherwise ignore it and do not auto-initialize.
<!-- zyes:end -->
```

### Global Zyes home (external mode)

```markdown
<!-- zyes-home:start -->
## Zyes home

Zyes external workflow root: `/absolute/path/to/zyes-home`.
<!-- zyes-home:end -->
```

Use lowercase kebab-case for the project name. Only one corresponding managed block may exist in a given file; update it in place when changing the path.

## CONTEXT.md starter

Create `knowledge/CONTEXT.md` with the skeleton below so later skills have a defined place to write into. Write the heading and prose in the language the user is conversing in, and translate the `_No entries yet._` placeholder too.

```markdown
# Project domain vocabulary

> Shared terms for this project. Only concepts specific to this project's domain — general engineering concepts don't belong here.

## Language

_No entries yet._
```

The `## Language` heading is the insertion point and the placeholder line marks the file as still empty. [z-domain](../z-domain/SKILL.md) deletes that line when it writes the first term — do not treat the starter as content that must be preserved.
