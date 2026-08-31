# Plan: Convergent Incremental Code Review

| Field           | Value                                                  |
|-----------------|--------------------------------------------------------|
| **Title**       | Convergent Incremental Code Review                     |
| **Spec**        | specs/convergent-incremental-code-review.md             |
| **Type**        | feature                                                |
| **Branch**      | feat/convergent-incremental-code-review                |
| **Implementer** | spec-implementer                                       |
| **Created**     | 2026-08-31 00:00:00                                    |
| **Status**      | IMPLEMENTED                                            |

## Context

The current review gate preserves spec-first safety but repeats complete spec
and quality reviews after narrow remediations. This change keeps the first
review complete and reviewers read-only, then uses self-contained envelopes,
validated baselines, targeted incremental/follow-up modes, grouped Important
findings, and a session-local two-round limit to make remediation converge.

The repository has no current `docs/architecture/map.md`; planning therefore
used direct repository exploration, and the missing map should be refreshed
separately with `/map force` if architecture documentation is wanted. No
Accepted or Proposed ADRs were found under `docs/adr/`. The plan assumes that
review state remains procedural state in the active implementation session;
it adds no persistence layer, plugin, framework, service, or agent.

## Stable Acceptance-Criterion IDs

These IDs are the stable mapping for this implementation and its review
envelopes. They preserve the approved criterion text in spec order without
depending on line numbers.

| ID | Approved requirement |
|----|----------------------|
| `AC-INITIAL-1` | First integrated review is complete, spec-first, and checks extra scope. |
| `AC-SEQUENCE-1` | Quality requires a fresh PASS for the same spec and reviewed baseline. |
| `AC-COVERAGE-1` | Initial quality covers the complete feature diff without reducing security or data-integrity coverage. |
| `AC-CRITERIA-1` | Acceptance criteria have stable descriptive IDs across rounds. |
| `AC-ENVELOPE-1` | Every reviewer invocation receives the complete self-contained envelope. |
| `AC-BLOCKED-1` | Missing, inconsistent, stale, invalid-baseline, or wrong-spec envelopes return BLOCKED without guessing. |
| `AC-INCREMENTAL-1` | A valid post-remediation baseline uses incremental spec review. |
| `AC-IMPACT-1` | Incremental review selects and explains direct and transitive criterion impact. |
| `AC-CARRY-1` | Valid unaffected criteria are carried forward and summarized by count. |
| `AC-FALLBACK-1` | Remediation gets extra-scope review and invalid carry-forward falls back to initial mode. |
| `AC-FINGERPRINT-1` | Spec or plan changes invalidate carry-forward. |
| `AC-FINDING-1` | Quality findings have stable IDs and group variants by invariant/root cause. |
| `AC-FINDING-2` | Important findings contain all required evidence and a root-cause remedy. |
| `AC-BATCH-1` | Initial Important findings are presented as one actionable batch. |
| `AC-FOLLOWUP-1` | Follow-up closes accepted IDs and checks only remediation regressions. |
| `AC-SEVERITY-1` | Only unresolved Important findings block integrated staging. |
| `AC-SCOPE-1` | Unrelated pre-existing issues and pure style preferences are excluded. |
| `AC-IDENTITY-1` | Equivalent recurring findings retain IDs and convergence accounting. |
| `AC-CONVERGENCE-1` | At most two remediation/follow-up rounds precede one explicit user decision. |
| `AC-REPORT-SPEC-1` | Spec reports are concise and preserve detailed MISSING/EXTRA handling. |
| `AC-REPORT-QUALITY-1` | Quality reports expose mode/status and follow-up resolution results. |
| `AC-EVIDENCE-1` | Reports avoid redundant restatement and unobserved evidence claims. |
| `AC-COMPAT-1` | Existing review policy, MISSING/EXTRA, ad-hoc ordering, and edit denial remain usable. |
| `AC-FILES-1` | Required skills and agents are assessed; optional files change only when required. |
| `AC-TESTS-1` | Deterministic coverage includes every review scenario required by the spec. |
| `AC-README-1` | README explains modes, envelopes, severity, batching, and convergence. |
| `AC-WORKFLOWS-1` | Existing define, plan, implement, review, and debug workflows remain usable. |

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`.
>
> Reference command (adapt `<base>` to the detected base):
>
> ```bash
> git checkout <base> && git pull --ff-only && git checkout -b feat/convergent-incremental-code-review
> ```
>
> If the repo is not a git workspace, branch creation is skipped and noted in
> the implementation report.

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
Each task maps to exactly one commit using
`<type>[(<scope>)]: <imperative description>`.

## Recommended Implementer

**Recommendation**: `spec-implementer`

The tasks are S/M, but baseline validity, transitive impact, finding identity,
permission boundaries, and bounded control flow require non-trivial design
judgment. The full implementer is appropriate despite the Markdown-oriented
implementation.

Run with `/implement` for `spec-implementer`.

## Build & Test Commands

The repository defines no separate build step.

| Action | Command |
|--------|---------|
| JSON validation | `python3 -m json.tool opencode.json >/dev/null` |
| Tests | `python3 -m unittest discover -s tests -p 'test_*.py'` |
| Diff hygiene | `git diff --check` |

## Tasks

### Task 1: Establish deterministic review-envelope contracts `[M | risk: data]`

**Goal**: Define one compact, session-local envelope and immutable baseline
contract shared by integrated and ad-hoc review calls.

**Risk rationale**: Fingerprints, changed-file boundaries, governing-document
identity, and carried review state determine whether prior evidence remains
valid; a mistaken contract could carry stale review data forward.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | create | Add deterministic text-contract tests for envelope fields, identity checks, fingerprints, and compatibility. |
| `skills/code-review/SKILL.md` | modify | Extend the existing input and gate contracts with envelope construction, validation, and mode-specific requirements. |
| `skills/spec-implement/SKILL.md` | modify | Make Step 5.5 construct and retain the envelope and baseline in the active session. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/code-review/SKILL.md` | Existing complete-diff/spec/plan/integrated-mode input contract and stale-result rule. |
| `skills/spec-implement/SKILL.md` | Existing Step 5 verification proof, fresh-review invalidation, and review-before-staging sequence. |
| `tests/test_configuration.py` | `unittest`, `Path.read_text()`, and deterministic Markdown/config contract assertions. |

**Steps**:

1. Add failing contract tests for all required envelope fields, including the
   exact spec path and slug, plan path, spec/plan content fingerprints, diff
   base, current tree/revision/diff fingerprint, complete mode-specific changed
   files, criterion map, affected criteria, previous spec result, prior quality
   dispositions, integrated/ad-hoc marker, and observed verification proof.
2. Define canonical session-local fingerprint procedures using deterministic
   SHA-256 content/diff inputs and sorted changed-file lists; capture immutable
   baseline values while allowing the current remediation fingerprint to
   advance. Do not add a utility, database, or persisted state file.
3. Require callers to construct the envelope for every invocation rather than
   relying on conversational context. Define mode-specific required/empty
   fields explicitly so ad-hoc calls can use an explicit ad-hoc governing-plan
   marker instead of fabricating an integrated plan.
4. Define consistency checks for mode, review ID, spec path/slug/fingerprint,
   plan fingerprint, diff base, current fingerprint, changed files, and prior
   reports. Missing or contradictory data returns concise `BLOCKED`; an
   invalid incremental baseline triggers the documented full-initial fallback
   rather than guessed carry-forward.
5. Carry Step 5 verification commands and concrete proof into the envelope;
   use an explicit unobserved marker when proof is unavailable.

**Tests**:

- Assert every required envelope field and integrated/ad-hoc distinction is
  present in both skill contracts.
- Cover missing fields, contradictory mode/state, wrong spec path or slug,
  stale current fingerprint, invalid diff base, and changed spec/plan
  fingerprints.
- Assert state remains session-local and no persistence/plugin/framework/new
  agent is introduced.
- Assert unobserved commands are never described as passing.

**Acceptance criteria covered**: `AC-ENVELOPE-1`, `AC-BLOCKED-1`,
`AC-FINGERPRINT-1`, `AC-EVIDENCE-1`, `AC-COMPAT-1`, `AC-WORKFLOWS-1`.

**Commit**: `feat(review): define session-local review envelopes`

---

### Task 2: Define stable criterion IDs and incremental spec review `[M | risk: data]`

**Goal**: Preserve complete initial review while adding validated criterion
impact selection, carry-forward, extra-scope checking, and safe fallback for
remediation reviews.

**Risk rationale**: Incorrect impact selection could omit a requirement
affected through a contract boundary or carry forward a stale compliance
result.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | modify | Add initial/incremental, stable-ID, impact, carry-forward, fallback, and report-shape tests. |
| `skills/code-review/SKILL.md` | modify | Define initial and incremental spec-review orchestration and concise outputs. |
| `skills/spec-implement/SKILL.md` | modify | Track initial PASS, remediation boundary, criterion impact reasons, and fallback in Step 5.5. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/code-review/SKILL.md` | Existing every-criterion/every-changed-behavior review and MISSING/EXTRA formats. |
| `skills/spec-implement/SKILL.md` | Existing rule that implementation or plan changes stale a prior report. |
| `skills/spec-plan/SKILL.md` | Existing plan acceptance-criteria mapping pattern and legacy-plan handling conventions. |

**Steps**:

1. Add failing tests proving `initial` mode reviews every criterion and all
   feature changes, checks extra scope, and retains complete security and
   data-integrity scrutiny.
2. Define explicit descriptive criterion IDs for new work. For legacy specs or
   plans without IDs, derive a deterministic session mapping from normalized
   criterion text plus a collision suffix, retain it while the spec
   fingerprint is unchanged, and do not rewrite the legacy documents.
3. Define `incremental` mode over the remediation diff since the accepted
   baseline. Require explicit impact reasons for direct changed behavior and
   transitive interface, permission, data, error, and output contract effects,
   plus related prior MISSING/EXTRA findings.
4. Carry forward only baseline-MET criteria proven unaffected under unchanged
   spec/plan fingerprints. If impact is uncertain, revalidate the criterion;
   if baseline validity cannot be established, fall back to `initial`.
5. Preserve MISSING and EXTRA outcomes, and always assess the remediation diff
   for newly introduced extra scope.
6. Replace successful full criterion restatement with the approved concise
   initial evidence groups and incremental one-line revalidation/count-only
   carry-forward formats. Keep detailed evidence for affected non-PASS
   criteria and MISSING/EXTRA only.

**Tests**:

- Cover full initial review, complete changed-work and extra-scope checks, and
  unchanged security/data-integrity coverage.
- Cover explicit and deterministic legacy criterion IDs, including collision
  handling and stability across unchanged rounds.
- Cover direct impact and every transitive category: interface, permission,
  data, error, and output contracts.
- Cover unaffected carry-forward, prior MISSING/EXTRA impact, uncertain-impact
  revalidation, invalid-base fallback, and spec/plan fingerprint fallback.
- Assert initial/incremental PASS formats are concise and non-PASS formats
  retain actionable MISSING and EXTRA detail.

**Acceptance criteria covered**: `AC-INITIAL-1`, `AC-COVERAGE-1`,
`AC-CRITERIA-1`, `AC-INCREMENTAL-1`, `AC-IMPACT-1`, `AC-CARRY-1`,
`AC-FALLBACK-1`, `AC-FINGERPRINT-1`, `AC-REPORT-SPEC-1`.

**Commit**: `feat(review): add incremental spec revalidation`

---

### Task 3: Bound quality remediation and finding lifecycle `[M | risk: other]`

**Goal**: Group quality defects under stable identities, batch user decisions,
target follow-ups, and stop automatic remediation after two rounds.

**Risk rationale**: The material risk is workflow convergence: identity drift,
one-at-a-time findings, or an off-by-one round counter could prolong or
prematurely end the mandatory review gate.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | modify | Add finding, batching, follow-up, severity, and convergence contract tests. |
| `skills/code-review/SKILL.md` | modify | Define quality modes, grouped evidence, IDs, severities, and output formats. |
| `skills/spec-implement/SKILL.md` | modify | Add batch decisions, dispositions, session-local counters, follow-up sequencing, and staging blockers to Step 5.5. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/code-review/SKILL.md` | Existing Important/Minor/Nitpick vocabulary and user fix/appeal/accept-risk decisions. |
| `skills/spec-implement/SKILL.md` | Existing user-decision gate, fresh spec rerun after changes, and no-staging-before-resolution rule. |
| `AGENTS.md` | YAGNI, no speculative abstraction, and epistemological-honesty constraints. |

**Steps**:

1. Add failing tests for stable finding IDs, invariant/root-cause grouping,
   required Important evidence, batch choices, follow-up boundaries, severity
   policy, repeated IDs, and exactly two remediation/follow-up rounds.
2. Define initial quality review as one unrestricted examination of the
   complete feature diff after the same-baseline spec PASS. Require each
   Important finding to include invariant, location, reachable path, impact,
   validation gap, significant variants, and one root-cause remedy.
3. Group related variants into one finding ID. Include the spec's archive-path
   variant checklist when that invariant is relevant; do not manufacture
   unrelated variants or identify findings by mutable line number alone.
4. Present all initial Important findings in one user interaction supporting
   fix all, selection by ID, appeal, and documented risk acceptance. Apply
   accepted fixes as one remediation batch where practical; Minor findings are
   advisory and integrated Nitpicks are hidden unless requested.
5. After incremental spec PASS, run `follow-up` only for accepted Important
   IDs and Important regressions reachable through the remediation diff. Do
   not reopen unchanged code or add unrelated Minor/Nitpick findings.
6. Keep finding IDs and dispositions in the active session. Match an equivalent
   recurrence by prior ID plus invariant/root cause; report uncertainty instead
   of silently merging unrelated findings.
7. Count each remediation plus targeted follow-up as one round, excluding the
   initial reviews. Allow rounds one and two only. If Important findings remain
   after round two, stop automatic iteration and ask once to accept risk,
   appeal IDs, revise implementation, revise spec/plan, or stop.
8. Make only unresolved Important findings block integrated staging. Preserve
   advisory all-requested-severity output for ad-hoc review and exclude
   untouched pre-existing issues and pure style preferences.

**Tests**:

- Cover grouped invariant variants, all Important evidence fields, and minimal
  root-cause remedies.
- Cover all-at-once Important presentation and fix-all/select/appeal/risk
  dispositions.
- Cover successful ID closure, an Important remediation regression, no
  unrestricted unchanged-code search, and no unrelated follow-up severity.
- Cover Minor advisory behavior, integrated Nitpick hiding, ad-hoc severity
  display, and untouched pre-existing issue exclusion.
- Cover equivalent-ID retention, no counter reset, rounds one/two, and the
  explicit decision after exhaustion.
- Assert the quality report contains review ID, mode, status, grouped findings,
  and concise successful follow-up closure results.

**Acceptance criteria covered**: `AC-FINDING-1`, `AC-FINDING-2`,
`AC-BATCH-1`, `AC-FOLLOWUP-1`, `AC-SEVERITY-1`, `AC-SCOPE-1`,
`AC-IDENTITY-1`, `AC-CONVERGENCE-1`, `AC-REPORT-QUALITY-1`.

**Commit**: `feat(review): bound grouped quality remediation`

---

### Task 4: Make reviewer prompts envelope-aware and mode-specific `[M | risk: security]`

**Goal**: Enforce the finalized envelope, mode, evidence, and report contracts
inside both read-only reviewer prompts without changing their models or tools.

**Risk rationale**: These prompts enforce the spec-first gate and edit-denied
permission boundary; a regression could allow a wrong-spec review, quality
before compliance, unsupported evidence, or reviewer mutation.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | modify | Add prompt, ordering, BLOCKED, evidence, permission, and model-lock tests. |
| `agents/review-spec.md` | modify | Validate envelopes and perform only initial or incremental spec review. |
| `agents/review-quality.md` | modify | Validate envelopes and perform only initial or targeted follow-up quality review. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `agents/review-spec.md` | Existing criterion evidence, MISSING/EXTRA, blocking, and no-quality-review instructions. |
| `agents/review-quality.md` | Existing fresh-PASS gate, changed-code boundary, evidence rules, and severity definitions. |
| `tests/test_configuration.py` | Existing agent frontmatter and permission assertions. |

**Steps**:

1. Add failing tests that lock both agents' current models, temperature, and
   `edit: deny`, `bash: deny`, `task: deny`, and `question: deny` permissions.
2. Require each reviewer to validate the complete envelope before inspecting
   code. On missing, contradictory, stale, invalid, or wrong-spec state, return
   concise `BLOCKED` naming the issue; never search for another spec or infer
   omitted state from repository files or conversation.
3. Teach `review-spec` the complete `initial` boundary and affected-only
   `incremental` boundary, including impact-selection explanations,
   carry-forward validation/count, remediation extra-scope review, fallback,
   and concise PASS/MISSING/EXTRA formats.
4. Teach `review-quality` to require a fresh spec PASS for the same spec,
   fingerprints, and reviewed state. Separate unrestricted `initial` behavior
   from ID-focused `follow-up` behavior and enforce grouped Important evidence.
5. Require both prompts to name only envelope-listed reviewed files and to
   distinguish observed proof from unobserved commands. Preserve initial
   security/data-integrity scrutiny and forbid reviewer fixes.

**Tests**:

- Assert exact permission and model assignments remain unchanged.
- Cover missing/inconsistent/wrong-spec/stale-envelope BLOCKED instructions.
- Assert quality cannot run before a fresh same-spec, same-baseline PASS.
- Assert initial and incremental/follow-up boundaries, fallback behavior,
  concise formats, and observed-evidence discipline are explicit.
- Assert neither reviewer edits, runs commands, delegates, asks questions, or
  reviews files outside the envelope.

**Acceptance criteria covered**: `AC-SEQUENCE-1`, `AC-COVERAGE-1`,
`AC-BLOCKED-1`, `AC-FINDING-2`, `AC-FOLLOWUP-1`, `AC-EVIDENCE-1`,
`AC-COMPAT-1`, `AC-FILES-1`.

**Commit**: `feat(review): enforce envelope-aware reviewer prompts`

---

### Task 5: Preserve ad-hoc review and planning-risk compatibility `[S | risk: other]`

**Goal**: Integrate the envelope with `/review` and existing risk-based review
selection without changing advisory behavior or legacy-plan safety.

**Risk rationale**: The material risk is compatibility across entry points:
making integrated fields mandatory in ad-hoc mode or changing authored-risk
rules would break established review and implementation workflows.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | modify | Add command and legacy/risk-policy compatibility tests. |
| `commands/review.md` | modify | Explain construction of an ad-hoc envelope from supplied diff and criteria. |
| `skills/code-review/SKILL.md` | modify | Clarify ad-hoc envelope defaults and advisory severity output. |
| `skills/spec-implement/SKILL.md` | modify | Preserve authored size/risk selection and conservative legacy-plan handling. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `commands/review.md` | Existing `agent: build`, pasted diff/criteria, sequential reviewers, and no-edit contract. |
| `skills/code-review/SKILL.md` | Existing mandatory/optional review matrix and ad-hoc behavior. |
| `skills/spec-implement/SKILL.md` | Existing legacy missing-risk warning, lite escalation, and full mandatory review. |
| `skills/spec-plan/SKILL.md` | Exact permitted risk categories and rule that risk comes from the approved plan. |

**Steps**:

1. Add failing tests preserving the command host, read-only advisory behavior,
   spec-first ordering, fresh-PASS quality gate, and user-supplied diff and
   criteria operation.
2. Have `/review` construct an explicit ad-hoc envelope from supplied content,
   with ad-hoc markers for unavailable integrated paths/state; reject missing
   ad-hoc essentials without requiring a nonexistent plan.
3. Allow ad-hoc users to request all severities while keeping the command
   advisory and preventing integrated blocking/remediation counters from
   taking control of the command.
4. Preserve mandatory review for L tasks, full-implementer M tasks, and
   security/data/concurrency/migrations risk; preserve the optional S/none
   offer and conservative behavior for legacy plans with missing risk.
5. Confirm that existing plans/specs without criterion IDs use Task 2's
   deterministic session mapping rather than failing or being rewritten.

**Tests**:

- Cover ad-hoc envelope construction, absent integrated plan fields, requested
  severity display, spec-first ordering, advisory output, and edit denial.
- Assert the existing risk matrix and legacy missing-risk behavior remain
  unchanged.
- Assert legacy criteria without IDs receive stable session IDs and continue
  through initial review.

**Acceptance criteria covered**: `AC-CRITERIA-1`, `AC-SEVERITY-1`,
`AC-COMPAT-1`, `AC-FILES-1`, `AC-WORKFLOWS-1`.

**Commit**: `docs(review): preserve ad-hoc and legacy compatibility`

---

### Task 6: Complete deterministic workflow coverage `[M | risk: other]`

**Goal**: Consolidate a readable scenario matrix proving every required
workflow contract and guarding unrelated workflows against regression.

**Risk rationale**: The material risk is incomplete deterministic coverage of
a prompt-driven workflow; tests must validate actionable contracts without
pretending Markdown string matches prove runtime feasibility.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | modify | Organize the complete required review scenario matrix and cross-file invariants. |
| `tests/test_configuration.py` | modify | Add only shared installation/config assertions that belong with existing configuration tests. |
| `tests/README.md` | modify | Document the review-contract suite and its evidentiary limits. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `tests/test_configuration.py` | Existing repository-path setup, text/config assertions, install checks, and `unittest` conventions. |
| `tests/test_document_ingest.py` | Existing deterministic fixture and ID-oriented test style where applicable. |
| `tests/README.md` | Existing repository validation command documentation. |

**Steps**:

1. Audit the behavior tests added in Tasks 1–5 against the approved scenario
   matrix and add any missing negative or cross-file case without introducing
   a workflow parser or generic fixture framework.
2. Ensure named coverage for initial review; incremental review; carry-forward;
   transitive impact; stale fallback; wrong-spec and missing-envelope
   rejection; grouped invariants; Important batching; targeted follow-up;
   Minor/Nitpick policy; repeated IDs; and the two-round limit.
3. Add cross-file invariants for spec-first ordering, same-spec fresh PASS,
   review-before-staging, reviewer edit denial, MISSING/EXTRA preservation,
   risk policy, concise outputs, and existing workflow availability.
4. Keep assertions semantic enough to catch missing contracts, but document
   that Markdown contract tests do not themselves prove test execution or
   runtime feasibility. Do not claim verification until commands are run and
   their results recorded.
5. Keep installation/config checks in `test_configuration.py`; keep detailed
   review scenarios in the focused test module. Do not alter document-workflow
   fixtures or tests.

**Tests**:

- Run the focused module with
  `python3 -m unittest tests.test_code_review_workflow`.
- Run the complete suite with
  `python3 -m unittest discover -s tests -p 'test_*.py'`.
- Confirm all scenarios named in `AC-TESTS-1` have explicit positive or
  negative assertions and no unrelated document test changed.

**Acceptance criteria covered**: `AC-TESTS-1`, `AC-SEQUENCE-1`,
`AC-REPORT-SPEC-1`, `AC-REPORT-QUALITY-1`, `AC-EVIDENCE-1`,
`AC-COMPAT-1`, `AC-WORKFLOWS-1`.

**Commit**: `test(review): cover convergent workflow contracts`

---

### Task 7: Document the convergent review workflow `[S | risk: none]`

**Goal**: Give users a concise explanation of review modes, envelopes,
blocking severity, batching, and bounded convergence.

**Risk rationale**: This is a bounded documentation update that does not alter
a security, data, concurrency, or migration boundary.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_code_review_workflow.py` | modify | Add README presence and scope-boundary assertions. |
| `README.md` | modify | Add concise user-facing review workflow documentation near the existing Tier 2 review section. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `README.md` | Existing Tier 2 review/debug inventory and concise workflow descriptions. |

**Steps**:

1. Add failing assertions for the required README topics before updating the
   document.
2. Explain `initial`, `incremental`, and `follow-up`, emphasizing that only
   repeated remediation review is narrowed and initial security/data-integrity
   coverage remains complete.
3. Summarize the self-contained envelope, stable IDs, stale/wrong-spec
   rejection, same-spec fresh-PASS gate, and session-local baseline.
4. Explain that only unresolved Important findings block integrated staging,
   Minor is advisory, Nitpick is hidden by default, and initial Important
   findings are decided as one batch.
5. Explain the maximum of two remediation/follow-up rounds and the explicit
   user decision on exhaustion. Preserve `/review` as read-only, spec-first,
   and advisory.
6. Leave installation and unrelated document workflows unchanged.

**Tests**:

- Assert README covers every required topic and does not describe reviewer
  fixes, persisted review state, or quality-before-spec behavior.
- Run the full repository suite to confirm existing README and document
  workflow expectations remain valid.

**Acceptance criteria covered**: `AC-README-1`, `AC-COMPAT-1`,
`AC-WORKFLOWS-1`.

**Commit**: `docs(readme): explain convergent code review`

---

**Task ordering**: Task 1 establishes the shared envelope and baseline. Task 2
adds incremental spec semantics; Task 3 adds quality lifecycle and convergence
on that baseline. Task 4 applies those finalized contracts to the reviewers.
Task 5 adapts compatibility entry points. Task 6 audits and completes the test
matrix, and Task 7 documents only stabilized behavior. Tasks are intentionally
sequenced because Tasks 1–5 touch overlapping workflow contracts.

## Edge Cases & Error Handling

- Missing or contradictory envelope field: return concise `BLOCKED` naming the
  field; do not reconstruct it from conversation or unrelated files (Tasks 1,
  4).
- Wrong spec path, slug, or fingerprint: return `BLOCKED`; never substitute a
  different spec (Tasks 1, 4).
- Changed spec or plan fingerprint, stale current state, or invalid diff base:
  invalidate carry-forward and perform a full initial review (Tasks 1, 2).
- Legacy criteria lack IDs: derive a deterministic collision-safe mapping for
  the session without rewriting approved legacy documents (Tasks 2, 5).
- Impact crosses an interface, permission, data, error, or output contract:
  include the transitively affected criterion; uncertainty favors
  revalidation, not carry-forward (Task 2).
- MISSING or EXTRA relates to remediation: include it in impact selection and
  preserve actionable non-PASS detail (Task 2).
- Related quality variants share a root cause: retain one stable finding ID and
  one invariant-level remedy (Task 3).
- Equivalent Important recurs: retain its prior ID and round count; do not
  disguise recurrence as a new finding (Task 3).
- Follow-up sees unrelated Minor/Nitpick or unchanged pre-existing code: omit
  it from the targeted integrated report (Task 3).
- Verification proof is absent: mark it unobserved and do not claim a pass
  (Tasks 1, 4, 6).
- Two remediation rounds end with unresolved Important findings: stop and ask
  for one explicit disposition instead of continuing automatically (Task 3).
- Ad-hoc review lacks integrated plan/session state: use explicit ad-hoc
  markers, keep the review advisory, and require only ad-hoc essentials (Task
  5).

## Verification

1. Run `python3 -m unittest tests.test_code_review_workflow` and record the
   exit code and passing-test count.
2. Run `python3 -m unittest discover -s tests -p 'test_*.py'` and record the
   exit code and passing-test count.
3. Run `python3 -m json.tool opencode.json >/dev/null` and record exit code 0;
   this confirms unchanged repository configuration remains valid JSON.
4. Run `git diff --check` and record exit code 0.
5. Inspect `git diff --name-only` and confirm changes are limited to the
   approved skills, agents, command, README, tests, spec, and plan; confirm no
   persistence layer, plugin, service, framework, model change, new agent, or
   unrelated document-workflow edit was introduced.
6. Verify both review agents still have edit-denied permissions and that
   `review-quality` is gated on a fresh same-spec PASS in both integrated and
   ad-hoc flows.
7. Trace one deterministic fixture or contract case through initial PASS,
   batched Important findings, incremental PASS with carry-forward, targeted
   follow-up, and the two-round stop, recording only directly observed proof.
