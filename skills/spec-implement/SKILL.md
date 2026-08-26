---
name: spec-implement
description: Use when the user wants to implement a spec or asks to invoke spec-implement. Reads specs/<slug>.md and plans/<slug>.md, then writes failing tests first (red), then code to pass them (green). Stages by default; commits only when the user explicitly asks in final review.
---

# Spec Implement

Implement a feature following strict TDD. Requires both a spec
(`specs/<slug>.md`) and a plan (`plans/<slug>.md`) produced by `spec-plan`.

## Workflow

### Step 1 — Load the Plan and Spec

Identify the slug. The user usually provides it; otherwise, list `plans/*.md`
via `glob` and ask via `question` which one to implement.

Read both files:

- `specs/<slug>.md`
- `plans/<slug>.md`

Verify the spec's **Status** is `PLANNED`. If it is `DRAFT`, the spec
was never finalised — stop and tell the user to finalise it first. If
the plan's **Status** is `DRAFT`, same: tell the user to finalise the
plan first. If the spec is `IMPLEMENTED`, confirm
re-implementation with the user via `question` before proceeding.

Use the same Markdown formatting rules in any `question` call as the
`spec-define` skill (no `a)` / `b)` markers; pass options via the tool's
`options` argument).

Extract from the plan:

- **Branch name** (e.g. `feat/my-feature`).
- **Build & Test Commands** (the table the planner produced).
- **Tasks** with their steps, files, and tests.
- Each task's **size and planner-authored risk tag**.
- **Acceptance criteria mapping**.
- **Edge cases**.

If a legacy task has no risk tag, warn the user and apply conservative
M-level handling. `spec-implementer-lite` must escalate; the full implementer
continues with mandatory review. Never infer a missing risk from the code.

### Step 2 — Confirm Build & Test Commands and Explore

**Extract build & test commands locally.** These are quick, local reads —
do them yourself, do not delegate:

- `package.json` — `scripts.test`, `scripts.build`.
- `pyproject.toml` — `[tool.pytest.ini_options]`, `[tool.poetry.scripts]`.
- `pom.xml` — `mvn test`, `mvn package`.
- `Cargo.toml` — `cargo test`, `cargo build`.
- `Makefile` — `make test`, `make build`.

If the plan's commands match what you find, use them. If they conflict, ask
the user via `question` which to use. If no test runner is detectable at
all, ask the user how to run tests before proceeding.

**Delegate broader codebase exploration** to the `explore` agent (a lighter
model) rather than doing `glob`/`grep`/`read` in-context. Call the `task`
tool with `subagent_type: explore` and ask for a compact digest of the code
structure, existing patterns, and testing conventions relevant to the plan's
tasks, so implementation can begin grounded in real files.

**Fallback:** if the `explore` agent is unavailable, fall back to in-context
`glob`/`grep`/`read` and note the fallback in the final report.

### Step 3 — Set Up the Branch

Check whether the workspace is a git repo:

```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```

If not a git repo, skip this step entirely and continue. Note in the
final report that no branch was created.

If inside a git repo, **detect the base branch automatically** in this
priority order — first match wins:

1. `develop` (local or remote) — for repos that use Git Flow.
2. `main` — modern default.
3. `master` — older repos.
4. Repo's symbolic `origin/HEAD` target, if set.
5. None of the above → fall back to the **current** branch and warn the
   user in the final report that no canonical base was found.

Detection commands (use what you need; treat `bash` failures non-fatal):

```bash
# Does a branch (local or remote) exist?
git show-ref --verify --quiet refs/heads/develop && echo local-develop
git ls-remote --exit-code --heads origin develop >/dev/null 2>&1 && echo remote-develop
# Same for main, master.

# Origin's default branch (resolved by `git remote set-head` or clone):
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null
```

Once you have picked a base branch:

```bash
git checkout <base>
git pull --ff-only   # tolerate failure if there is no upstream / no network
git checkout -b <branch-name-from-plan>
```

Do NOT create a `develop` branch on the user's behalf. If `develop` does
not already exist, the project is not using Git Flow; respect that.

Handling uncommitted spec/plan files on the base branch: typical case is
that `specs/<slug>.md` and `plans/<slug>.md` are sitting uncommitted on
the user's current branch when you start. The `git checkout` commands
above will carry uncommitted files across to the new branch because
they don't exist on the base. If `git checkout` refuses due to a real
conflict (rare — only if a file with the same path already exists on
the base branch), stop and ask the user via the `question` tool how to
proceed; do not stash, reset, or discard their work without explicit
permission.

Record in the final report which base branch was used (e.g.
"Branched from `main`" or "No git remote, branched from local `main`").

If the plan's `Branch` field encodes a Git Flow assumption that doesn't
match this repo (e.g. plan says branch from `develop`, but the repo only
has `main`), use the detected base anyway — the plan's branch *name*
(e.g. `feat/<slug>`) is still valid; only the *parent* changes.

### Step 4 — Implement Task by Task (Red → Green)

Work through the plan's tasks in order. For each task:

**4a. Write failing tests (Red)**

Write all tests for this task before touching production code. Follow the
project's existing test conventions (file location, naming, framework).

Run the tests and confirm they fail for the right reason:

```bash
<test command from Step 2>
```

If the tests fail for the wrong reason (compilation error, wrong import,
missing dependency unrelated to the new code), fix that first. Do not move
on to 4b until the tests are genuinely red on the right assertion.

A new test failing on its intended assertion is expected TDD red and must not
invoke the `debug` skill.

**4b. Implement the code (Green)**

1. Write only the code needed to make the failing tests pass — no more.
2. Do not modify test files during this phase except to correct genuine
   mistakes (wrong import path, typo in assertion value). Note any such
   corrections for the final report.
3. After each meaningful step, run the test command again. A failure is
   unexpected when a previously-passing test regresses, the message is
   genuinely unexplained rather than the new test's intended assertion, or
   the same unexplained failure remains after one normal correction attempt.
4. When any unexpected-failure indicator occurs, automatically invoke the
   `debug` skill and block Step 4b. Do not continue until either the root cause
   is named with evidence and a failing regression test is added, or the
   bounded debug workflow escalates.
5. After successful diagnosis, resume the minimal green implementation for
   the same task. On escalation, return the evidence and wait for the user's
   decision; do not guess, weaken tests, or silently continue.
6. All tests for this task must pass before starting the next task.

Repeat from 4a for each task in the plan.

### Step 5 — Verify Build & Tests Pass

Run the full test suite (and the full build, if the plan defines a build
command) one final time. Both must exit with code 0. If either fails,
diagnose and fix before proceeding. Do not weaken or skip tests.

Do not declare verification or implementation success without recording for
each test/build action:

- the exact command;
- exit code 0;
- a substantiating proof line: a non-zero passing-test count or a concrete
  build-artifact path.

If a command cannot produce either proof form, run the approved manual checks
and record a concrete non-zero scenario/check count with the decisive output.
An exit code alone is not proof.

### Step 5.5 — Run the Code-Review Gate

Determine review policy only from each plan task's authored size and risk:

- review is mandatory for every L-sized task;
- review is mandatory for every M-sized task handled by the full implementer;
- review is mandatory for any task tagged `security`, `data`, `concurrency`,
  or `migrations`, regardless of size;
- for an S-sized task tagged `risk: none`, use `question` to offer review; it
  is optional, and a declined review must be recorded for the final summary;
- if risk is missing, warn and apply the conservative handling from Step 1:
  lite escalates and the full implementer performs mandatory review.

Never infer risk. Any listed sensitive domain makes review mandatory.

For each required or accepted review, invoke the `code-review` skill with the
complete diff, spec criteria, and plan. It runs `review-spec` first and may run
`review-quality` only after a fresh spec `PASS`.

On `MISSING` or `EXTRA`, return the spec report and ask the user to choose
whether to fix code, fix the plan, or override the review. Do not auto-fix.
After any change, discard stale reports and rerun spec review before quality.

Return quality findings to the implementer/user for a fix, appeal, or accept
decision. Reviewers never edit. Do not proceed to staging until all mandatory
review decisions and verification proof are complete.

### Step 6 — Stage Changes

If inside a git repo, stage all created, modified, and deleted files using
**explicit paths only**:

```bash
git add <path1> <path2> ...
```

**Never use `git add .` or `git add -A`.** List every file.

Confirm with:

```bash
git status
```

Do not commit yet.

### Step 6.5 — Final Review with the User

Before finishing, give the user one last chance to request changes or to
ask you to commit. Call `question` with a concise summary that covers:

- Tasks completed (from the plan).
- Files created, modified, and deleted (the same paths you staged).
- Tests added and their current status (all green).
- Build/test commands used, each exit code, and each substantiating proof line:
  a non-zero passing-test count or a concrete build-artifact path.
- Anything noteworthy — test corrections made, deviations from the plan,
  skipped git steps, etc.

Phrase the question so all three answers are equally easy:

> All tasks are complete and tests pass. Files staged:
>
> - `path/a`
> - `path/b`
>
> Reply:
>
> - "looks good" — I will stop here without committing.
> - "commit" — I will commit using the message from the plan: `<message>`.
> - "commit: <your message>" — I will commit with your message instead.
> - Anything else — I will treat it as a change request and address it.

Pass the three explicit choices via the `question` tool's `options`
argument when possible; the free-form change-request path is the
"anything else" fallback.

After calling `question`, stop immediately and wait for the user's reply.

- **If the user requests changes**: address them. New behaviour requires
  new failing tests first (return to Step 4 for the affected task).
  Re-run tests, re-stage with explicit paths, then return to Step 6.5
  and ask again.
- **If the user says "looks good"**: do not commit. Proceed to Step 7.
- **If the user says "commit"**: run `git commit -m "<message from plan>"`,
  then proceed to Step 7.
- **If the user says "commit: <message>"**: run `git commit -m "<message>"`,
  then proceed to Step 7.

If there is no git repo, the commit options are obviously inapplicable —
omit them from the question.

### Step 7 — Update Status and Report

1. Use `edit` to update the **Status** row in `specs/<slug>.md` from
   `PLANNED` to `IMPLEMENTED`.
2. Use `edit` to update the **Status** row in `plans/<slug>.md` from
   `PLANNED` to `IMPLEMENTED`.
3. Send a one-line summary to the user, e.g.:
   `Implementation complete. specs/<slug>.md and plans/<slug>.md set to IMPLEMENTED.`

Do not suggest next steps.

## Guidelines

- **Always run Step 6.5 before finishing.** The user must have an explicit
  chance to request changes or to ask for a commit. Never commit without
  this step.
- **TDD is non-negotiable.** Tests must be confirmed red before any
  production code is written.
- **Green means all tests pass.** Do not proceed if any tests fail.
- **Test files may be corrected, never weakened.** The only valid reason to
  edit a test during the green phase is to fix a genuine mistake (wrong
  import, typo). Note any such change in the final report.
- **Stay within the spec.** Implement only what the spec and plan describe.
- **Stage with explicit paths.** Never `git add .` or `git add -A`.
- **No commits unless asked.** The user owns commits.
- **Fix the root cause.** An unexpected Step 4b failure invokes `debug` and
  blocks implementation until evidence names the cause or the bounded process
  escalates. Never suppress or weaken tests.
- **Git is optional.** If no git repo is found, skip all git commands and
  note it in the report.
- **Do not suggest next steps.**
