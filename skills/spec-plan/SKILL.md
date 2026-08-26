---
name: spec-plan
description: Use when the user wants to plan a spec, create an implementation plan, or invokes spec-plan. Reads an approved specs/<slug>.md, explores the codebase, and produces a task-by-task plan at plans/<slug>.md.
---

# Spec Plan

Create a technical implementation plan from an existing spec definition.
Output is `plans/<slug>.md`.

## Workflow

### Step 1 — Load the Spec

Identify the slug. The user usually says it directly, or names the file. If
unclear, list `specs/*.md` (use `glob`) and ask the user via `question`
which one to plan.

Read `specs/<slug>.md` with the `read` tool.

Verify the spec's **Status** is `DEFINED` or `PLANNED`. If it is
`DRAFT`, the spec was never finalised — stop and tell the user to
finalise the spec first (re-run the spec-definer if needed). If it is
`IMPLEMENTED`, ask the user for confirmation before re-planning:

> This spec is already implemented. Re-plan anyway?

Extract from the spec: **Title**, **Type**, **Scope**, and **slug** — needed
for branch naming and the plan filename.

### Step 2 — Explore the Codebase

Delegate codebase exploration to the `explore` agent (a lighter model)
rather than doing `glob`/`grep`/`read` in-context. This keeps the
planner's context focused on planning and lets the exploration run once.

Call the `task` tool with `subagent_type: explore`. Ask it to return a
compact digest that grounds the plan in real files:

- **Project structure** — key directories, entry points, config files.
- **Existing code & patterns** — utilities, conventions, and any code
  related to the spec that a task should reuse rather than reinvent.
- **Testing conventions** — test framework, test file locations, naming.
- **Build & test commands** — read from manifest files (`package.json`,
  `pyproject.toml`, `pom.xml`, `Cargo.toml`, `Makefile`) so the plan's
  Build & Test Commands table is accurate.

Give the explore agent the spec so it knows what to look for, and ask for
a structured summary (file inventory, patterns, testing framework, build
commands, relevant code) rather than raw file dumps.

**Fallback:** if the `explore` agent is unavailable, fall back to
in-context `glob`/`grep`/`read` and read-only `bash` (`ls`, `find`,
`cat`), and note the fallback in the plan or to the user.

You may ask up to 3 clarifying technical questions via the `question` tool.
After each call, stop and wait. Use the same Markdown formatting rules as
the `spec-define` skill (no `a)` / `b)` markers; pass options via the tool's
`options` argument).

Do not propose new abstractions when suitable implementations already exist
in the codebase.

### Step 3 — Draft the Plan

Use this structure. Omit any section with no content.

```text
# Plan: <Spec Title>

| Field        | Value                              |
|--------------|------------------------------------|
| **Title**    | <title from spec>                  |
| **Spec**     | specs/<slug>.md                    |
| **Type**     | <type from spec>                   |
| **Branch**   | <type-prefix>/<slug>               |
| **Implementer** | <spec-implementer \| spec-implementer-lite> |
| **Created**  | <YYYY-MM-DD HH:mm:ss>              |
| **Status**   | DRAFT                              |

## Context

<Why this change is being made — condensed from the spec into 2–3 sentences.>

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. The branch
> name is `<type-prefix>/<slug>` (see mapping below).
>
> Reference command (the implementer adapts to the detected base):
>
> ```bash
> git checkout <base> && git pull --ff-only && git checkout -b <type-prefix>/<slug>
> ```
>
> If the repo is not a git workspace, branch creation is skipped and
> noted in the implementation report.

Branch type mapping:

- feature → `feat/<slug>`
- bug → `fix/<slug>`
- refactor → `refactor/<slug>`
- chore → `chore/<slug>`

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Each task in the Tasks section maps to exactly one
commit.

## Recommended Implementer

**Recommendation**: `<spec-implementer | spec-implementer-lite>`

<One or two sentences justifying the choice against the criteria below.>

Run with `/implement` for `spec-implementer`, or `/implement-lite` for
`spec-implementer-lite`.

## Build & Test Commands

| Action | Command |
|--------|---------|
| Test   | <e.g. `npm test`, `pytest`, `mvn test`>     |
| Build  | <e.g. `npm run build`, `mvn package`>       |

(Derive these from the project's manifest files. Omit the build row if the
project has no build step.)

## Tasks

### Task 1: <Task title> `[S/M/L | risk: <none/security/data/concurrency/migrations>]`

**Goal**: <One sentence — what this task achieves.>

**Risk rationale**: <Why `none` or the listed domain applies.>

**Files**:

| File                | Action                   | Description     |
|---------------------|--------------------------|-----------------|
| `path/to/file`      | create / modify / delete | What changes    |

**Reuse**:

| File                | What to reuse                       |
|---------------------|-------------------------------------|
| `path/to/existing`  | Existing function or pattern        |

**Steps**:

1. <What to do and why>

**Tests**:

- What to test (unit, integration), test file locations, key scenarios.

**Acceptance criteria covered**: <Which spec criteria this task satisfies.>

**Commit**: `<type>[(<scope>)]: <description>`

---

(Repeat for each task.)

**Task ordering**: <Dependencies, or note that tasks are independent.>

## Edge Cases & Error Handling

- <Edge case>: <How it will be handled> (Task N)

## Verification

1. <Step to run/test the changes>
2. <Step to confirm acceptance criteria are met>
```

Save the draft to disk first, then ask the user to review it.

**Important — never embed the full plan markdown inside a `question`
tool call.** Tool-call payloads have practical size limits and large
embedded markdown causes timeouts and aborted tool executions. Always
write the file first, then keep the `question` text short.

Steps:

1. Use the `write` tool to save the full plan markdown to
   `plans/<slug>.md` with the **Status** row set to `DRAFT`. (You will
   flip it to `PLANNED` only after the user approves in Step 4.)
2. Call `question` with a **short** message — no embedded markdown:

   > I've written a draft plan to `plans/<slug>.md`. Please open it
   > and review.
   >
   > Quick summary:
   >
   > - <one-line overview of what the plan does>
> - <number of tasks>, sized: <count of S> S, <count of M> M,
>   <count of L> L
> - Risk assignments: <task-to-risk summary for user approval>
   > - <one-line note on branch and base>
   > - Suggested implementer: `<spec-implementer | spec-implementer-lite>`
   >   — <short reason>
   >
   > Reply `looks good` to finalise, or describe any changes you want
   > (including a different implementer tier).

3. If the plan contains any `L` tasks, call them out in the summary
   bullets and ask whether they should be split.
4. Require the user to approve the planner-authored risk assignments with the
   rest of the plan; do not defer risk selection to implementation.
5. If the user requests changes, **edit `plans/<slug>.md` directly**
   using the `edit` tool (do not rewrite the whole file unless you
   really mean to), then call `question` again with a short summary
   of what changed. Repeat until the user approves.

Do not paste the plan contents into chat unless the user explicitly
asks you to. The file on disk is the source of truth during review.

### Step 3.5 — Recommend an Implementer Tier

Once the tasks are drafted, you know enough to recommend which implementer
agent should do the work. Fill in the **Implementer** row and the
**Recommended Implementer** section of the plan.

Recommend `spec-implementer-lite` (cheap model) only when **all** hold:

- Every task is sized `S` or `M` — no `L` tasks.
- The work is mechanical and low-risk: config changes, scaffolding,
  straightforward CRUD, copy/text edits, simple single-page UI.
- No concurrency, cryptography, security boundaries, database migrations,
  or performance optimisation.
- The existing patterns to follow are already clear from exploration; the
  implementer will not need to make significant design decisions.

Recommend `spec-implementer` (full model) if **any** hold:

- Any task is sized `L`, or the plan has many interdependent tasks.
- The work involves subtle logic, non-obvious edge cases, or design
  judgement.
- It touches concurrency, crypto, auth/security, migrations, or
  performance.
- The spec's acceptance criteria are hard to verify mechanically.

When it is genuinely borderline, recommend `spec-implementer` — the cost of
a failed cheap run plus escalation exceeds the saving.

### Task Risk Tags

Every task header must contain one planner-authored risk value:

- `none` when no listed sensitive domain applies;
- `security`, `data`, `concurrency`, or `migrations` when that domain applies;
- a comma-separated set only when multiple listed domains genuinely apply.

Risk is independent from size: size estimates effort, while risk controls the
implementation review gate. The planner assigns and explains risk from the
approved spec and codebase evidence; it is never inferred by the implementer.
Include all risk assignments in the Step 3 approval summary.

A legacy plan may omit the risk field. `spec-implement` warns about the
missing risk and applies conservative M-level handling: the lite implementer
escalates, while the full implementer performs mandatory review. New plans
must never omit the field.

Surface this recommendation in the Step 3 review question so the user can
override it before implementation starts.

### Step 4 — Finalise the Plan

The plan file is already on disk from Step 3 with Status `DRAFT`.
Once the user has approved (replied `looks good` or equivalent):

1. Use `edit` to flip the **Status** row in `plans/<slug>.md` from
   `DRAFT` to `PLANNED`.
2. Use `edit` to update the **Status** row in `specs/<slug>.md` from
   `DEFINED` to `PLANNED`.
3. Send a one-line confirmation, e.g.:
   `Plan finalised at plans/<slug>.md (Status: PLANNED). Spec status updated.`

If the project is a git repo, append a one-line warning to the
confirmation message:

> Note: leave `specs/<slug>.md` and `plans/<slug>.md` uncommitted on
> the current branch. The spec-implementer will create a feature
> branch from your repo's base branch and carry these files onto it
> automatically. Committing the spec/plan to your base branch (e.g.
> `develop` or `main`) before implementation runs is usually not
> what you want.

Do not perform any git operations yourself — branch creation is the
spec-implementer's job. Do not suggest next steps.

## Guidelines

- **Ground every step in the codebase.** Reference actual files and
  functions found during exploration.
- **Respect the spec boundary.** Cover everything in the spec and nothing
  outside it.
- **Aim for S/M tasks.** Split aggressively. Mark `L` only when a task
  genuinely cannot be split — explain why.
- **Author risk explicitly.** Keep it separate from size, explain it, and
  include it in the user's plan approval.
- **Warn the user about `L` tasks** during the review step.
- **Keep steps atomic.**
- **Follow Conventional Commits.** Every task must include a planned commit
  message.
- **Omit empty sections.**
- **Never flip the Status to PLANNED before the user approves the draft.**
  The DRAFT file is written to disk first (Step 3); only the status flip
  waits on approval (Step 4).
