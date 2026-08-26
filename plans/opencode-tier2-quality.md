# Plan: Opencode Tier 2: Code Review and Debugging

| Field | Value |
|-------|-------|
| **Title** | Opencode Tier 2: Code Review and Debugging |
| **Spec** | specs/opencode-tier2-quality.md |
| **Type** | chore |
| **Branch** | chore/opencode-tier2-quality |
| **Implementer** | spec-implementer |
| **Created** | 2026-08-26 13:18:55 |
| **Status** | IMPLEMENTED |

## Context

Tier 1 established global governance, delegated exploration, and command infrastructure, but `spec-implement` still lacks structured handling for unexpected failures and a review gate between green tests and completion. This change adds evidence-first debugging, sequential spec and quality review, explicit planner-authored risk tags, and standalone `/review` and `/debug` entry points without allowing reviewer subagents to modify code.

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. The branch
> name is `chore/opencode-tier2-quality`.
>
> Reference command (the implementer adapts to the detected base):
>
> ```bash
> git checkout <base> && git pull --ff-only && git checkout -b chore/opencode-tier2-quality
> ```
>
> The currently detected base is `main`. If the repo is not a git
> workspace, branch creation is skipped and noted in the implementation
> report.

Branch type mapping:

- feature → `feat/<slug>`
- bug → `fix/<slug>`
- refactor → `refactor/<slug>`
- chore → `chore/<slug>`

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Each task in the Tasks section maps to exactly one commit.

## Recommended Implementer

**Recommendation**: `spec-implementer`

Although every task is S or M sized and changes configuration or Markdown, the sequential review gate, failure classification, bounded escalation, and compatibility behavior for legacy plans require non-trivial judgment. Use `/implement`; `spec-implementer-lite` must escalate when these M-sized workflow changes are present.

## Build & Test Commands

| Action | Command |
|--------|---------|
| Validate JSON | `python -m json.tool opencode.json` |
| Validate discovery | `opencode run "list agents, skills, and commands"` |

This repository has no package manifest, build step, or automated test framework. The implementer must supplement the commands above with the manual workflow checks in Verification and record each command, exit code, and proof line.

## Tasks

### Task 1: Register locked review subagents `[S | risk: none]`

**Goal**: Register read-only spec and quality reviewers with explicit, non-inherited model assignments.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `agents/review-spec.md` | create | Define the read-only spec reviewer with its locked model and prompt |
| `agents/review-quality.md` | create | Define the read-only quality reviewer with its locked model and prompt |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `agents/spec-implementer.md` | Existing agent-file frontmatter, full provider/model identifier, and permission-map syntax |
| `agents/spec-implementer-lite.md` | Existing Haiku provider/model identifier |

**Steps**:

1. Create `agents/review-spec.md` as a `subagent`, explicitly pinning `model: ibm-ica/claude-haiku-4-5` for cost-controlled acceptance-criteria checking.
2. Create `agents/review-quality.md` as a `subagent` and explicitly pin `model: ibm-ica/gpt-5.6-sol`; do not omit this property because an unpinned subagent inherits its caller's model.
3. Move each complete reviewer prompt into its agent-file body and preserve temperature and all permissions in YAML frontmatter.
4. Deny edits for both reviewers and permit only the read/search operations needed to inspect diffs and referenced files; reviewers report findings and never fix them.
5. Keep `opencode.json` lean and leave its existing `explore` and `general` overrides unchanged.

**Tests**:

- Parse `opencode.json`, confirm it remains valid JSON, and confirm neither reviewer is defined inline.
- Load the OpenCode agent inventory and verify both reviewer names are discoverable as subagents.
- Inspect the loaded definitions to prove `review-spec` uses Haiku, `review-quality` uses `ibm-ica/gpt-5.6-sol`, and both deny edits.

**Acceptance criteria covered**: Reviewer subagent registration; locked Haiku/GPT-5.6 Sol assignments; subagent mode; edit-deny behavior; clear failure rather than silent review skipping when a reviewer is unavailable.

**Commit**: `chore(config): register locked review subagents`

---

### Task 2: Create the sequential code-review skill `[M | risk: none]`

**Goal**: Define a mandatory-order review workflow that proves spec compliance before spending a GPT-5.6 Sol review on quality.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/code-review/SKILL.md` | create | Document the two-reviewer workflow, structured reports, trigger rules, and escalation behavior |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-implement/SKILL.md` | Existing numbered workflow, hard-gate, `question`, and final-review wording conventions |
| `AGENTS.md` | Existing YAGNI, error-handling, duplication, naming, and project-convention standards |
| `agents/review-spec.md` and `agents/review-quality.md` | Task 1 reviewer names, prompts, and explicit model/permission assignments |

**Steps**:

1. Create a discoverable `code-review` skill, approximately 150 lines, that accepts a diff plus acceptance criteria and invokes `review-spec` first.
2. Require `review-spec` to evaluate every criterion and all changed work, returning a structured `PASS`, `MISSING`, or `EXTRA` report with criterion citations and code locations; `PASS` requires both complete coverage and no work outside the spec.
3. Stop immediately on `MISSING` or `EXTRA`, return only the actionable spec report, do not invoke `review-quality`, and require the caller to wait for a user decision to fix code, fix the plan, or override.
4. Only after `PASS`, invoke `review-quality` and require a GPT-5.6 Sol-authored report covering readability, duplication, error handling, coupling, and naming, with each finding classified as Important, Minor, or Nitpick and paired with a location and remedy.
5. Return both reports to `spec-implement` for a fix, appeal, or accept decision; on any missing/unavailable reviewer, fail clearly rather than silently bypassing the gate.
6. Document integration at Step 5.5: mandatory for L-sized tasks and tasks tagged `security`, `data`, `concurrency`, or `migrations`; optional and explicitly offered for S-sized `risk: none` tasks; M-sized tasks are handled by the full implementer with mandatory review.
7. Document ad-hoc mode for `/review`: criteria and diff may be supplied directly, results are advisory, but spec-first ordering still applies.

**Tests**:

- Exercise a compliant diff and confirm `review-spec` runs before `review-quality` and both structured reports return.
- Exercise a missing criterion and a YAGNI addition independently; confirm `MISSING`/`EXTRA` cites evidence and quality review does not run.
- Exercise quality findings at all three severities and confirm each contains a code location and remedy.
- Make a reviewer unavailable and confirm the skill reports an explicit blocking error.

**Acceptance criteria covered**: Code-review skill; PASS/MISSING/EXTRA output; Important/Minor/Nitpick output; spec-compliance-first gate; risk integration; unavailable-subagent handling; ad-hoc review behavior.

**Commit**: `feat(code-review): add sequential review gate`

---

### Task 3: Create the evidence-first debug skill `[M | risk: none]`

**Goal**: Provide a bounded debugging method that prohibits speculative fixes and exits only with evidence or an explicit escalation.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/debug/SKILL.md` | create | Define reproduce, isolate, name, and fix phases for integrated and standalone debugging |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-implement/SKILL.md` | Existing red/green test discipline, no-test-weakening rule, and escalation interaction style |
| `AGENTS.md` | Existing epistemological honesty and no-silent-failure rules |

**Steps**:

1. Create a discoverable standalone `debug` skill, approximately 80 lines, with the hard rule that no fix may be attempted before the root cause is named with evidence.
2. Define four ordered phases: reproduce deterministically, isolate through bisection or controlled hypothesis tests, name the root cause and cite evidence, then apply the minimal fix with a failing regression test.
3. Bound isolation to three bisection attempts or hypothesis cycles; preserve the commands, outputs, and ruled-out hypotheses for escalation.
4. Define integrated success as root cause plus evidence and a regression test, after which `spec-implement` resumes Step 4b; define failure as escalation without guessing or weakening tests.
5. Define standalone `/debug` behavior for pasted errors without spec context: reproduce/isolate/name or escalate, but do not modify code or attempt a fix because implementation remains the user's or spec-implementer's responsibility.

**Tests**:

- Walk through a reproducible regression and confirm a fix is forbidden until evidence names the cause and a failing regression test exists.
- Walk through an unresolved failure and confirm escalation occurs after three bounded cycles with tested and ruled-out hypotheses.
- Invoke the workflow without plan/spec context and confirm it returns evidence or escalation without editing files.

**Acceptance criteria covered**: Standalone debug skill; four-phase method; root-cause-first rule; bounded attempts; integrated and standalone exit conditions; no guessing or test weakening.

**Commit**: `feat(debug): add evidence-first debugging workflow`

---

### Task 4: Add standalone review and debug commands `[S | risk: none]`

**Goal**: Expose read-only ad-hoc review and debugging through command files that follow the existing command convention.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `command/review.md` | create | Route `/review` to `spec-implementer` with diff and criteria input |
| `command/debug.md` | create | Route `/debug` to `build` with error or failing-output input |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `command/implement.md` | Existing agent frontmatter and concise command-body pattern |
| `command/implement-lite.md` | Existing description of routing and escalation behavior |
| `skills/code-review/SKILL.md` | Task 2 ad-hoc input and advisory-output contract |
| `skills/debug/SKILL.md` | Task 3 standalone no-spec and no-edit contract |

**Steps**:

1. Create `command/review.md` with frontmatter routing to `spec-implementer`; accept a pasted diff and acceptance criteria and explicitly invoke the code-review skill in advisory, read-only mode.
2. Create `command/debug.md` with frontmatter routing to the general-purpose `build` agent; accept an error message or failing test output and explicitly invoke the standalone debug mode without requiring plan context.
3. State in each command body that standalone operation must not edit application files; only the edit-denied review subagents may be launched by `/review`, while `/debug` stops after evidence or escalation.
4. Rely on the repository's existing `command/*.md` and `skills/*/SKILL.md` auto-discovery pattern rather than inventing unsupported registration keys in `opencode.json`.

**Tests**:

- Load the command inventory and confirm `/review` routes to `spec-implementer` while standalone `/debug` routes to `build`.
- Invoke `/review` with pasted code and criteria and verify sequential advisory reports with no edits.
- Invoke `/debug` with pasted output and no spec and verify evidence-first analysis with no edits.

**Acceptance criteria covered**: `/review` and `/debug` shortcuts; distinct workflow and standalone routing; standalone inputs; read-only behavior; skill and command discovery.

**Commit**: `feat(commands): add review and debug shortcuts`

---

### Task 5: Add planner-authored risk tags `[S | risk: none]`

**Goal**: Make review risk explicit in every newly planned task while keeping it independent from effort size.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/spec-plan/SKILL.md` | modify | Add risk to task headers, drafting guidance, and plan-review confirmation |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-plan/SKILL.md` | Existing task template, S/M sizing rules, implementer recommendation, and draft approval question |
| `agents/spec-implementer-lite.md` | Existing escalation categories for security, concurrency, and migrations |

**Steps**:

1. Change the task template header to `### Task N: <title> [S/M/L | risk: <none/security/data/concurrency/migrations>]`.
2. Define risk as one explicit planner-authored value (or a comma-separated set when multiple listed domains genuinely apply), never inferred by the implementer; define size solely as effort.
3. Require the planner to assign and explain risk during drafting and include risk assignments in the user's approval summary.
4. Document that a missing risk tag in a legacy plan is treated conservatively by `spec-implement` as M-level handling: lite escalates and the full implementer performs mandatory review with a warning.
5. Update examples and guidelines consistently so no old size-only task-header instruction remains.

**Tests**:

- Inspect the complete skill for stale `[S/M/L]`-only task header examples.
- Draft representative `none`, single-domain, and multi-domain task headers and verify risk remains distinct from size.
- Confirm plan review asks the user to approve authored risks rather than deferring inference to implementation.

**Acceptance criteria covered**: Plan task risk field; planner ownership; user approval; size/risk independence; legacy missing-tag behavior.

**Commit**: `chore(spec-plan): add explicit task risk tags`

---

### Task 6: Integrate unexpected-failure debugging `[M | risk: none]`

**Goal**: Narrowly route genuine regressions from Step 4b into blocking evidence-first debugging without disrupting expected TDD red failures.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/spec-implement/SKILL.md` | modify | Replace generic Step 4b mystery handling with explicit debug triggers and exits |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-implement/SKILL.md` | Existing Step 4a red confirmation, Step 4b green loop, no-test-weakening guidance, and question-based escalation |
| `skills/debug/SKILL.md` | Task 3 trigger contract, bounded investigation, evidence requirement, and exit states |

**Steps**:

1. Preserve Step 4a as the expected red phase and state explicitly that a new test failing on its intended assertion must not invoke debug.
2. In Step 4b, define unexpected failure narrowly as a previously passing test regressing, a genuinely unexplained failure rather than the new test's expected assertion, or the same unexplained failure remaining after one normal correction attempt.
3. Automatically invoke the debug skill when that trigger is met and block further implementation until either the root cause is named with evidence and a failing regression test is added, or the bounded workflow escalates.
4. On successful diagnosis, resume the minimal green implementation; on escalation, return the evidence to the user/full implementer and wait rather than guessing, weakening tests, or silently continuing.
5. Align the Guidelines section with the new Step 4b contract and remove the existing generic list of guessed causes where it would undermine root-cause-first behavior.

**Tests**:

- Simulate a normal RED assertion and confirm debug is not invoked.
- Simulate each of the three narrow unexpected-failure indicators and confirm debug blocks Step 4b.
- Confirm successful diagnosis requires evidence and a regression test; confirm unresolved diagnosis waits after escalation.

**Acceptance criteria covered**: Step 4b narrow trigger; automatic blocking debug invocation; TDD-red distinction; success and escalation exits; prohibition on weakening tests.

**Commit**: `feat(spec-implement): integrate evidence-first debugging`

---

### Task 7: Add review and verification gates `[M | risk: none]`

**Goal**: Enforce risk-driven review before staging and require reproducible proof before any success declaration.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/spec-implement/SKILL.md` | modify | Add Step 5.5 review gate, strengthen Step 5 proof, and reconcile downstream references |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-implement/SKILL.md` | Existing Step 5 full verification, Step 6 staging, Step 6.5 user decision, and Step 7 status update |
| `skills/code-review/SKILL.md` | Task 2 gate order, reports, unavailable-reviewer behavior, and appeal paths |
| `skills/spec-plan/SKILL.md` | Task 5 task-header risk contract |
| `agents/spec-implementer-lite.md` | Existing lite escalation section and full-implementer handoff report |

**Steps**:

1. Extend plan loading to extract each task's size and explicit risk tag; when risk is missing, warn, apply M-level handling, and require lite to escalate while full `spec-implementer` performs mandatory review.
2. Strengthen Step 5 so success is forbidden without the exact command, exit code, and substantiating proof line: a non-zero passing-test count or a concrete build-artifact path. Use the same wording in Step 6.5's summary requirements to prevent drift.
3. Insert Step 5.5 after full verification and before Step 6 staging, invoking code review mandatorily for every L-sized task, M-sized task handled by the full implementer, or task tagged `security`, `data`, `concurrency`, or `migrations`.
4. For S-sized `risk: none` tasks, use `question` to offer review without requiring it; if declined, record the decision for the final audit summary and continue.
5. On `MISSING` or `EXTRA`, return the spec report and wait for the user's fix-code, fix-plan, or override decision; discard any stale quality report and rerun spec review after changes. Only invoke quality after a fresh spec `PASS`.
6. Return quality findings for the implementer/user to fix, appeal, or accept; reviewers never make changes themselves.
7. Keep Step 6, Step 6.5, and Step 7 numbering stable, update all internal references, and ensure staging and final status changes cannot happen before review and proof gates complete.

**Tests**:

- Exercise L-sized, M-sized, sensitive-domain, S/none, and missing-risk tasks; verify mandatory, optional, declined-and-logged, and conservative paths respectively.
- Trigger `MISSING`/`EXTRA`, change the implementation, and confirm spec review reruns before a new quality review.
- Confirm no success path reaches staging without a command, exit code 0, and pass-count or artifact proof.
- Inspect all step references in `skills/spec-implement/SKILL.md` and both implementer agent files for coherence with Steps 5, 5.5, 6, 6.5, and 7; update an agent reference only if the inserted gate makes it inaccurate.

**Acceptance criteria covered**: Step 5.5 review integration; all risk/size trigger paths; missing-risk compatibility; review escalation and rerun; verification proof gate; coherent sequencing; audit logging for declined optional review.

**Commit**: `feat(spec-implement): enforce review and verification gates`

---

**Task ordering**: Task 1 must precede Task 2 so the named reviewers and locked models exist. Tasks 2 and 3 may then proceed independently. Task 4 depends on Tasks 2 and 3; Task 6 depends on Task 3; Task 7 depends on Tasks 2 and 5. Recommended order: 1 → 2 → 3 → 4 → 5 → 6 → 7.

## Edge Cases & Error Handling

- **Expected TDD red versus regression**: A new test failing on its intended assertion remains in Step 4a; only the three documented Step 4b indicators invoke debug. (Task 6)
- **No root cause after bounded attempts**: Stop after three bisection or hypothesis cycles and return evidence and ruled-out causes; never guess or weaken a test. (Tasks 3, 6)
- **Spec review does not pass**: Return `MISSING` or `EXTRA`, skip quality, wait for user direction, and rerun spec review after changes. (Tasks 2, 7)
- **Reviewer unavailable**: Fail the review gate with a named configuration/discovery error; never silently skip mandatory review. (Tasks 1, 2, 7)
- **Quality model inheritance**: `review-quality` explicitly pins `ibm-ica/gpt-5.6-sol`; omission is a validation failure because it would inherit the caller's model. (Task 1)
- **Missing legacy risk tag**: Warn and treat it as M-level handling; lite escalates, while full implementation requires review. (Tasks 5, 7)
- **Optional S/none review declined**: Continue but preserve the user's decision in the final summary. (Task 7)
- **Standalone commands lack spec context**: `/review` uses supplied criteria and remains advisory; `/debug` stops after naming the cause with evidence or escalation and performs no fix. (Tasks 3, 4)
- **Multiple risk domains**: Use a comma-separated list only when the task genuinely touches more than one enumerated domain; any listed sensitive domain makes review mandatory. (Tasks 5, 7)
- **No automated test runner**: Use JSON validation, OpenCode discovery, and isolated manual scenarios; report exact commands, exits, and proof instead of claiming unverified success. (All tasks)

## Verification

1. Run `python -m json.tool opencode.json`; record exit code 0 and parsed output as configuration proof.
2. Run `opencode run "list agents, skills, and commands"`; record exit code and proof lines showing `review-spec`, `review-quality`, `code-review`, `debug`, `/review`, and `/debug` are discoverable.
3. Inspect loaded reviewer configuration and confirm both are subagents with edits denied, `review-spec` pins `ibm-ica/claude-haiku-4-5`, and `review-quality` explicitly pins `ibm-ica/gpt-5.6-sol` rather than inheriting the caller model.
4. Run code-review fixtures for PASS, MISSING, and EXTRA; prove quality runs only after PASS and that quality output classifies located remedies as Important, Minor, or Nitpick.
5. Run debug fixtures for expected TDD red, diagnosed regression, and unresolved regression; prove expected red bypasses debug, diagnosed regression has evidence plus a regression test, and unresolved work escalates after three cycles without guessing.
6. Exercise Step 5.5 with L, M, sensitive-domain, S/none, declined optional, and missing-risk tasks; record the observed gate decision for each.
7. Invoke `/review` with a pasted diff and criteria and `/debug` with pasted failure output outside spec context; verify both remain read-only and return the documented standalone result.
8. Perform a final coherence read across `skills/spec-plan/SKILL.md`, `skills/spec-implement/SKILL.md`, both reviewer agent files, both new skills, both commands, and `opencode.json`; map every acceptance criterion to a verified behavior and confirm all internal step references agree.
