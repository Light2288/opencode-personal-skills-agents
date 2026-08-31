# Plan: Add Repository Audit Workflow

| Field        | Value                              |
|--------------|------------------------------------|
| **Title**    | Add Repository Audit Workflow      |
| **Spec**     | specs/add-repository-audit-workflow.md |
| **Type**     | feature                            |
| **Branch**   | feat/add-repository-audit-workflow |
| **Implementer** | spec-implementer                |
| **Created**  | 2026-08-31 00:00:00                |
| **Status**   | IMPLEMENTED                        |

## Context

The repository has a deliberately diff-based `/review` workflow, but no
advisory workflow for assessing pre-existing repository health when a worktree
is clean or dirty. This plan adds the smallest separate `/audit` path, codifies
global progress-update deduplication, and protects both contracts with
deterministic tests while leaving the existing review command, skill,
reviewers, and model assignments unchanged.

Acceptance criteria are referenced below as **AC-01** through **AC-11** in
their existing order in `specs/add-repository-audit-workflow.md:73-83`.

No architecture map exists at `docs/architecture/map.md`, so architecture-map
context is unavailable and normal repository exploration was used. No
Accepted or Proposed ADRs exist under `docs/adr/`. The absence of an
architecture map does not block this configuration-only change.

### Design Decisions

- Add a dedicated `review-audit` subagent. Reusing `review-spec` is unsafe
  because it requires acceptance criteria; reusing `review-quality` is unsafe
  because its contract explicitly excludes pre-existing code outside a diff.
  One dedicated reviewer is the smallest design that keeps responsibilities
  clear.
- Assign the new reviewer `ibm-ica/gpt-5.6-sol`, matching the judgment-heavy
  quality-review role. Do not alter `review-spec`, `review-quality`, or any
  other existing model assignment.
- Keep `bash` denied for the reviewer. The host audit workflow discovers and
  runs only permitted non-destructive commands, then supplies observed results
  to the reviewer; shell access must not weaken edit denial.
- Reuse the existing severity vocabulary and order: `Important`, `Minor`,
  `Nitpick`; classify optional improvements separately as `Improvement`, after
  defects. Stable `AUDIT-*` IDs derive from normalized finding identity
  (kind, invariant/concern, path, and root cause), never line number alone.
- Keep discovery and remediation separate. `/audit` may ask which stable IDs
  the user wants to address and return a self-contained selected-findings
  handoff, but it neither edits nor invokes an implementer. Any edit-capable
  work proceeds separately through the existing spec/plan implementation
  workflow.
- A dirty-worktree check is attribution context only, never an audit scope
  boundary. No runtime service, persistence, plugin, registry, or generic
  orchestration layer is introduced.

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. The branch
> name is `feat/add-repository-audit-workflow`.
>
> Reference command (the implementer adapts to the detected base):
>
> ```bash
> git checkout <base> && git pull --ff-only && git checkout -b feat/add-repository-audit-workflow
> ```
>
> If the repo is not a git workspace, branch creation is skipped and
> noted in the implementation report.

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Each task below maps to exactly one commit.

## Recommended Implementer

**Recommendation**: `spec-implementer`

The work has no large task, but it establishes a security-relevant read-only
boundary and requires careful separation of audit, review, command execution,
and later implementation. The full implementer is appropriate for these
non-obvious workflow contracts.

Run with `/implement` for `spec-implementer`.

## Build & Test Commands

| Action | Command |
|--------|---------|
| Validate JSON | `python3 -m json.tool opencode.json >/dev/null` |
| Test all contracts | `python3 -m unittest discover -s tests -p 'test_*.py'` |
| Test audit contracts | `python3 -m unittest tests.test_repository_audit_workflow` |
| Check optional document dependencies | `python3 tools/document_ingest.py check-dependencies` |
| Optional installed-discovery smoke check | `opencode run "list agents, skills, and commands"` |

No build step or build manifest exists. `install.sh` is covered through its
isolated temporary-`HOME` contract test rather than writing to the developer's
real OpenCode configuration.

## Tasks

### Task 1: Define the audit workflow contract `[M | risk: other]`

**Goal**: Add the separate `/audit` entry point and repository-audit skill,
including deterministic scenario coverage for audit scope, evidence, output,
and handoff behavior.

**Risk rationale**: The material risk is workflow conflation: an imprecise
contract could accidentally make audit diff-bound, treat unobserved checks as
proof, or cross into automatic remediation.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `commands/audit.md` | create | Route `$ARGUMENTS` from `/audit` to the audit skill and state its advisory scope. |
| `skills/repository-audit/SKILL.md` | create | Define instruction-first discovery, host validation, reviewer envelope, findings, no-findings output, and selected-ID handoff. |
| `tests/test_repository_audit_workflow.py` | create | Add deterministic command/skill and fixture-driven workflow contract tests. |
| `tests/fixtures/repository_audit/scenarios.json` | create | Encode clean, dirty, whole, scoped, evidence, ordering, no-findings, and handoff scenarios. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `commands/review.md` | Minimal command frontmatter, `$ARGUMENTS` routing, and advisory wording without copying its diff gate. |
| `skills/code-review/SKILL.md` | Stable-ID, severity-order, `Findings: NONE`, user-selection, and session-local disposition patterns while keeping audit inputs distinct. |
| `skills/doc-analyze/SKILL.md` | Evidence-versus-inference and source-location discipline. |
| `tests/test_code_review_workflow.py` | Standard-library `unittest`, normalized section assertions, and fixture-driven scenario patterns. |

**Steps**:

1. Write failing contract tests and JSON scenarios for clean and dirty
   worktrees; missing diff and criteria; default whole-repository scope;
   directory and concern scope; instruction-first inspection; applicable audit
   concerns; and dirty-state attribution that does not bound review.
2. Add scenarios for observed pass/failure results, unavailable or unpermitted
   commands, and unobserved recommendations. Require the report to distinguish
   each state and forbid claims that an unrun command passed.
3. Contract the deterministic output: defects ordered `Important`, `Minor`,
   then `Nitpick`; optional `Improvement` items reported separately; stable
   `AUDIT-*` identity independent of line movement; path and line evidence;
   impact; minimal remedy; limitations; and exact `Findings: NONE` when no
   concrete issue exists.
4. Define `/audit` and its optional directory/concern input without requiring
   a diff or acceptance criteria. Require project `AGENTS.md` and other
   discoverable instructions/conventions to be inspected before code.
5. Define host-owned discovery of available non-destructive validation
   commands and an audit envelope that labels observed command/result evidence
   separately from recommendations the host could not run.
6. Keep audit advisory: after reporting, ask for selected stable IDs and emit
   a self-contained handoff for a separate spec/plan-driven edit-capable phase;
   never edit, auto-select, invoke implementation, or persist findings.

**Tests**:

- In `tests/test_repository_audit_workflow.py`, assert command routing,
  optional scope/concern, no diff/criteria prerequisite, instruction-first
  sequence, all required concern categories, and no-fix language.
- Drive `tests/fixtures/repository_audit/scenarios.json` cases for clean/dirty,
  whole/scoped, observed/unobserved/unavailable verification, deterministic
  severity and evidence formatting, stable IDs, exact no-findings output, and
  selected-only handoff.

**Acceptance criteria covered**: AC-01, AC-02, AC-03, AC-04, AC-06, AC-07,
AC-08, AC-10

**Commit**: `feat(audit): define repository audit workflow`

---

### Task 2: Add the dedicated edit-denied audit reviewer `[M | risk: security]`

**Goal**: Add one repository-wide audit reviewer with an explicit read-only
permission boundary and no overlap with diff acceptance review.

**Risk rationale**: Reviewer shell or edit access could violate the advisory
boundary or mutate audited data; permissions and responsibility separation are
therefore security-sensitive.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `agents/review-audit.md` | create | Define whole-repository audit responsibilities, evidence rules, model, and edit-denied tools. |
| `skills/repository-audit/SKILL.md` | modify | Name and validate the dedicated reviewer and define the host-to-reviewer envelope. |
| `tests/test_repository_audit_workflow.py` | modify | Assert reviewer discovery, model, permissions, scope, and host-owned validation. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `agents/review-quality.md` | `mode: subagent`, temperature-zero, `ibm-ica/gpt-5.6-sol`, and read/glob/grep-only permission shape. |
| `agents/review-spec.md` | Explicit invalid-input and evidence-bound reporting style, not its acceptance gate. |
| `tests/test_configuration.py` | Existing frontmatter and denied-tool assertion patterns. |

**Steps**:

1. First add failing tests requiring `review-audit` to allow only `read`,
   `glob`, and `grep`, while denying `edit`, `bash`, `task`, and `question`.
2. Create the reviewer with model `ibm-ica/gpt-5.6-sol` without changing any
   existing reviewer file or model assignment.
3. Scope it to pre-existing whole-repository correctness, security, data
   integrity, error handling, maintainability, duplication, coupling, naming,
   tests, configuration, and documentation consistency where applicable.
4. Require it to consume host-observed worktree and validation evidence,
   report unsupported coverage as a limitation, and never fabricate a finding
   or execute a command itself.
5. Make the skill block clearly if the named reviewer is unavailable; do not
   fall back to either diff reviewer.

**Tests**:

- Assert exact allowed and denied tools, subagent mode, temperature, and the
  new model assignment.
- Assert the skill invokes `review-audit`, never substitutes `review-spec` or
  `review-quality`, and keeps command execution in the host workflow.
- Assert existing reviewer model and permission declarations remain unchanged.

**Acceptance criteria covered**: AC-03, AC-04, AC-05, AC-08, AC-10

**Commit**: `feat(audit): add read-only audit reviewer`

---

### Task 3: Protect the existing review gate `[S | risk: other]`

**Goal**: Add explicit regression contracts proving `/review` remains
diff-based, acceptance-criteria-first, sequential, and read-only.

**Risk rationale**: The material compatibility risk is accidental weakening
or routing of the established acceptance gate while adding a nearby workflow.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_repository_audit_workflow.py` | modify | Add cross-workflow non-regression assertions. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `commands/review.md` | Existing diff-and-acceptance-criteria command contract. |
| `skills/code-review/SKILL.md` | Mandatory diff, criteria, spec-first sequencing, and advisory rules. |
| `tests/test_code_review_workflow.py` | Existing detailed review contracts; reference rather than duplicate their full suite. |

**Steps**:

1. Add cross-workflow tests asserting `/audit` does not route through
   `code-review` and `/review` does not route through `repository-audit`.
2. Assert `/review` still requires both complete diff and acceptance criteria,
   runs `review-spec` before `review-quality`, and does not fix findings.
3. Assert the implementation leaves `commands/review.md`,
   `skills/code-review/SKILL.md`, `agents/review-spec.md`, and
   `agents/review-quality.md` behavior and model declarations intact.

**Tests**:

- Run the new cross-workflow test class plus the existing complete
  `tests/test_code_review_workflow.py` suite.

**Acceptance criteria covered**: AC-01, AC-05, AC-08, AC-10

**Commit**: `test(review): preserve diff acceptance gate`

---

### Task 4: Codify global progress-update deduplication `[S | risk: other]`

**Goal**: Add one global communication policy and deterministic contracts for
kickoff, materially new updates, silence, combination, and final-response
deduplication.

**Risk rationale**: The material behavioral risk is ambiguous wording that
causes agents either to spam repeated conclusions or suppress genuine blockers
and changed evidence.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `AGENTS.md` | modify | Add concise global progress-update rules applicable to all agents. |
| `tests/test_repository_audit_workflow.py` | modify | Add deterministic progress-policy contract assertions and scenarios. |
| `tests/fixtures/repository_audit/scenarios.json` | modify | Encode kickoff, repeated, combined, materially new, blocker, plan-change, and user-decision cases. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `AGENTS.md` | Existing concise-output and epistemological-honesty sections and terminology. |
| `agents/document-worker.md` | Existing restraint around progress-message evidence. |

**Steps**:

1. Add a focused section to root `AGENTS.md`: at most one kickoff per related
   exploration phase; combine related discoveries; continue silently without
   new information; update only for materially new evidence, blockers, changed
   plans, or user decisions.
2. Explicitly prohibit restating or paraphrasing an already communicated
   conclusion and prohibit repeating progress conclusions in the final
   response, while retaining concise factual communication.
3. Add fixture-driven contracts for one kickoff, suppression of repeated and
   paraphrased conclusions, combined related evidence, silence without change,
   and allowed updates for each of the four material triggers.

**Tests**:

- Assert all four permitted subsequent-update triggers and one-kickoff limit.
- Assert repeat/paraphrase suppression, discovery combination, silent
  continuation, and final-response non-repetition.

**Acceptance criteria covered**: AC-09, AC-10

**Commit**: `docs(agents): deduplicate progress updates`

---

### Task 5: Document and validate audit installation `[S | risk: none]`

**Goal**: Document `/audit` versus `/review` and prove the existing installer
discovers and copies the new command, skill, and agent without new machinery.

**Risk rationale**: No sensitive domain applies; this is documentation and
mechanical installation-contract coverage using existing sync behavior.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `README.md` | modify | Concisely document selection, scope, read-only behavior, finding format, and implementation handoff. |
| `tests/test_configuration.py` | modify | Extend command routing and isolated installer expectations for audit artifacts. |
| `tests/test_repository_audit_workflow.py` | modify | Add README contract assertions. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `README.md` | Existing command, workflow, agent, and installation tables/sections. |
| `install.sh` | Existing `rsync` of `commands/`, `skills/`, `agents/`, and `AGENTS.md`; no installer code change is needed. |
| `tests/test_configuration.py` | `CommandRoutingMixin` and temporary-`HOME` installer tests. |

**Steps**:

1. Add a concise comparison explaining that `/review` requires a diff and
   acceptance criteria, whereas `/audit` accepts clean or dirty repositories,
   defaults to whole-repository scope, and permits an optional directory or
   concern.
2. Document audit's advisory/read-only guarantee, evidence and verification
   distinctions, severity-ordered stable finding format, exact no-findings
   result, and selected-findings handoff to a separate implementation phase.
3. Extend command-routing tests for `commands/audit.md` and isolated installer
   tests to verify `audit.md`, `repository-audit/SKILL.md`, and
   `review-audit.md` are copied by unchanged `install.sh` behavior.
4. Assert no `opencode.json` registration, service, persistence, plugin, or
   orchestration layer was added and existing model declarations remain
   unchanged.

**Tests**:

- Assert README contains the `/audit`/`/review` distinction and complete but
  concise audit contract.
- Run installer tests with temporary `HOME` and verify all three new artifacts
  are discoverable without modifying `install.sh`.
- Run JSON validation and the full test suite.

**Acceptance criteria covered**: AC-01, AC-02, AC-04, AC-06, AC-07, AC-08,
AC-10, AC-11

**Commit**: `docs(audit): document workflow and installation`

**Task ordering**: Task 1 establishes the audit contract; Task 2 supplies its
reviewer; Task 3 locks the adjacent `/review` boundary; Task 4 establishes the
global communication rule; Task 5 documents and validates the complete
installed workflow. Implement each task test-first and commit only when its
targeted contracts pass.

## Edge Cases & Error Handling

- Clean worktree: proceed without diff or acceptance criteria and audit the
  selected repository scope. (Task 1)
- Dirty worktree: record dirty status for attribution, but never narrow
  discovery to changed lines. (Task 1)
- Directory or concern supplied: validate and apply the requested scope;
  report an invalid or unreadable path as a limitation rather than silently
  reverting to whole-repository scope. (Task 1)
- Instructions missing or unreadable: report the limitation and rely only on
  conventions that can be verified. (Tasks 1–2)
- Validation unavailable, denied, or failing: report the exact observed state;
  do not label an unrun command as passing or infer a defect solely from its
  absence. (Tasks 1–2)
- No concrete issue: emit exactly `Findings: NONE`; do not convert speculative
  improvements into defects. (Task 1)
- Imprecise evidence location: use the best verifiable repository reference
  and state the limitation, otherwise omit the unsupported finding. (Tasks
  1–2)
- Reviewer unavailable: block with an explicit configuration error; never
  substitute a diff reviewer. (Task 2)
- Finding selection: include only user-selected IDs in the handoff and make no
  edit or implementation call. (Task 1)
- Repeated progress conclusion: remain silent unless new evidence, a blocker,
  a changed plan, or a user decision exists. (Task 4)

## Verification

1. Run `python3 -m unittest tests.test_repository_audit_workflow` and confirm
   clean/dirty, whole/scoped, instruction-first, evidence, verification,
   formatting, permissions, handoff, review-preservation, and progress cases
   pass deterministically.
2. Run `python3 -m unittest tests.test_code_review_workflow` and confirm the
   existing diff/acceptance-criteria/spec-first contracts remain green.
3. Run `python3 -m unittest tests.test_configuration` and confirm routing,
   unchanged model declarations, and temporary-`HOME` installation pass.
4. Run `python3 -m json.tool opencode.json >/dev/null` and confirm the unchanged
   configuration remains valid.
5. Run `python3 -m unittest discover -s tests -p 'test_*.py'` for the complete
   deterministic suite.
6. Run `python3 tools/document_ingest.py check-dependencies`; record its actual
   result separately because optional dependencies are not audit proof.
7. Optionally run `opencode run "list agents, skills, and commands"` in an
   installed environment and verify `/audit`, `repository-audit`, and
   `review-audit` discovery; label this as an observed smoke result only if it
   is actually executed.
8. Inspect the implementation diff and confirm there are no changes to
   `commands/review.md`, `skills/code-review/SKILL.md`, `agents/review-spec.md`,
   `agents/review-quality.md`, `opencode.json`, or `install.sh`, and no runtime
   state service, persistence, plugin, generic orchestration layer, or unrelated
   workflow change.
