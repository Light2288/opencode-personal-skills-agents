# Convergent Incremental Code Review

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Convergent Incremental Code Review                     |
| **Type**      | feature                                                |
| **Scope**     | spec-implementation and code-review workflow           |
| **Created**   | 2026-08-31 00:00:00                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

The existing spec-implementation review gate is safe but inefficient and can
fail to converge. It always repeats a complete spec review after a quality
finding is fixed, even when only a narrow remediation changed. It then runs
another unrestricted quality review. This repeats unchanged acceptance
criteria and feature-diff inspection, consumes unnecessary latency and
context, and can reveal one adjacent variant of the same defect per loop.

Review calls can also lose the governing spec, plan, changed-file boundary,
or prior-review context. Reviewers may consequently evaluate the wrong spec or
claim evidence they did not observe. The workflow has no explicit bounded
convergence policy beyond user acceptance or agent step exhaustion.

## Current Behavior

The integrated workflow runs `review-spec` before `review-quality`, and the
quality reviewer is gated on a fresh spec PASS. After remediation invalidates
that PASS, the workflow repeats a full spec review and then an unrestricted
quality review. Findings are not consistently grouped around shared
invariants, and Minor or Nitpick findings can extend the remediation loop.
Reviewers are intended to remain read-only, but each invocation does not yet
have a required, self-contained envelope establishing all governing context.

## Desired Outcome

Implement a convergent review workflow while preserving the existing
spec-first safety rule and read-only reviewers. The workflow has three explicit
modes:

- **`initial`**: perform one complete review of every acceptance criterion and
  all feature changes, including extra-scope checking, followed by one
  unrestricted quality review after spec PASS. Group related defects by
  invariant or root cause and return all known Important findings together.
- **`incremental`**: after remediation, inspect only the remediation diff,
  revalidate directly or transitively affected criteria, carry forward
  unaffected criteria from a valid baseline PASS, and check remediation
  changes for extra scope. Fall back to a full initial review when the
  baseline is not valid.
- **`follow-up`**: after incremental spec PASS, verify closure of prior
  accepted Important finding IDs and inspect the remediation diff for
  Important regressions introduced by those fixes. Do not restart an
  unrestricted search through unchanged code or introduce unrelated Minor or
  Nitpick findings.

Every reviewer invocation receives a compact, self-contained review envelope
so it never depends on conversational memory. The integrated workflow batches
accepted Important findings, permits at most two remediation/follow-up rounds
after the initial review, and stops for an explicit user decision when the
limit is exhausted. Only unresolved Important findings block staging; Minor
findings remain advisory, and Nitpicks are hidden by default in integrated
mode.

## Acceptance Criteria

- [ ] The first integrated review performs a complete spec-first review of
  every acceptance criterion and all feature changes, including extra-scope
  checking, before any quality review.
- [ ] `review-quality` cannot run in integrated mode unless a fresh spec PASS
  for the same governing spec and reviewed baseline has been established.
- [ ] The initial quality review examines the complete feature diff and does
  not reduce existing security or data-integrity coverage.
- [ ] Stable descriptive acceptance-criterion IDs are assigned before the
  first review and remain consistent across review rounds unless the user
  explicitly approves a spec change.
- [ ] Every reviewer invocation receives a self-contained envelope containing:
  review mode; review ID; exact governing spec path and slug; governing plan
  path; spec and plan fingerprints; diff base; current revision/tree/diff
  fingerprint; complete changed-file list for that mode; stable acceptance
  criteria; affected criteria; previous spec result when carrying criteria
  forward; prior quality finding IDs and dispositions; integrated/ad-hoc mode;
  and observed verification commands and proof when available.
- [ ] Reviewers return a concise BLOCKED result without guessing when the
  envelope is missing fields, internally inconsistent, stale, unable to
  establish a valid baseline, or references a different spec.
- [ ] After remediation, the workflow uses incremental spec review when the
  baseline spec PASS remains valid.
- [ ] Incremental spec review inspects only the remediation diff, revalidates
  criteria directly or transitively affected through changed interfaces,
  permission boundaries, data/error/output contracts, or related MISSING and
  EXTRA findings, and identifies why the affected criteria were selected.
- [ ] Unaffected criteria are carried forward only when spec and plan
  fingerprints are unchanged, the baseline passed, and the remediation does
  not affect them directly or transitively; successful reports summarize them
  by count rather than restating them individually.
- [ ] Incremental review checks the remediation diff for newly introduced
  extra scope, and any invalid carry-forward condition falls back to a full
  initial spec review.
- [ ] Spec or plan changes invalidate carry-forward and force a full initial
  review.
- [ ] Quality findings are evidence-based, have stable IDs, and group related
  variants under one violated invariant or root cause rather than emitting
  isolated examples.
- [ ] Each Important finding includes severity, violated invariant, concrete
  location, reachable input or execution path, concrete impact, why existing
  validation misses it, significant variants considered, and one minimal
  root-cause remedy.
- [ ] Initial quality review presents all known Important findings to the user
  as one batch, allowing fix-all, selection by finding ID, appeal, or documented
  risk acceptance.
- [ ] Follow-up quality review verifies closure of prior accepted Important
  finding IDs and checks only the remediation diff for Important regressions;
  it does not reopen unchanged code or add unrelated Minor or Nitpick findings.
- [ ] Only unresolved Important findings block integrated staging. Minor and
  Nitpick findings are advisory; they do not automatically trigger
  remediation or another mandatory review cycle, and Nitpicks are hidden by
  default in integrated mode.
- [ ] Pre-existing unrelated issues and pure style preferences are excluded
  unless the feature touches, introduces, or materially worsens them.
- [ ] An equivalent recurring finding retains its existing finding ID and does
  not reset the remediation-round counter.
- [ ] The integrated workflow permits at most two remediation/follow-up rounds
  after the initial review, then stops automatic iteration and requests one
  explicit user decision: accept remaining risk, appeal findings, revise the
  implementation, revise the spec or plan, or stop implementation.
- [ ] Successful initial and incremental spec reports use the specified
  concise formats, include their review/baseline fingerprints, and provide
  detail only for MISSING or EXTRA findings and affected criteria when not
  passing.
- [ ] Quality reports use the specified status and finding format; successful
  follow-ups identify resolved finding IDs and whether an Important
  remediation regression was found.
- [ ] Reports do not restate the full specification, unchanged criteria, or
  plan tasks unless a mismatch exists, and do not claim tests or runtime
  evidence that was not directly observed or supplied.
- [ ] Existing MISSING and EXTRA handling, risk-based decisions about whether
  review is mandatory, integrated spec-first ordering, ad-hoc `/review`
  read-only behavior, and edit-denied review subagents remain usable.
- [ ] The required workflow and documentation changes assess at least
  `skills/code-review/SKILL.md`, `skills/spec-implement/SKILL.md`,
  `agents/review-spec.md`, and `agents/review-quality.md`; related command,
  planning-risk, test/fixture, and README changes are made only as required.
- [ ] Deterministic tests or fixtures cover initial full review, incremental
  review, unaffected-criterion carry-forward, transitive impact, stale
  baseline fallback, wrong-spec rejection, grouped invariant findings,
  batched Important findings, targeted follow-up, Minor/Nitpick policy,
  repeated IDs, convergence limits, and missing envelope fields.
- [ ] README documentation explains review modes, envelope requirements,
  blocking severity policy, batching, and convergence behavior.
- [ ] Existing define, plan, implement, review, and debug workflows remain
  usable, and no unrelated document workflow is modified.

## Edge Cases & Error Handling

- Missing, contradictory, stale, or wrong-spec envelope: return BLOCKED with
  the missing or inconsistent field; do not reconstruct state or review a
  different spec.
- Changed spec or plan fingerprint: invalidate the prior baseline and run a
  full initial spec review; do not carry criteria forward.
- Remediation crosses an interface, permission, data, error, or output
  contract: treat transitively affected criteria as affected and revalidate
  them.
- Remediation cannot establish a valid diff base or baseline: fall back to a
  full initial review rather than performing an unsafe incremental review.
- A previously reported Important finding recurs or is equivalent: preserve
  its finding ID and remediation-round accounting.
- Several variants share one invariant: group them into one finding and list
  the variants considered, including relevant archive path and partial-write
  variants where applicable.
- A quality review discovers only Minor or Nitpick issues: report them
  according to the requested mode, but do not block staging or trigger an
  automatic remediation cycle; hide Nitpicks by default in integrated mode.
- A remediation introduces an Important regression: report it in targeted
  follow-up, retain prior finding identities, and count it against the bounded
  remediation policy.
- The remediation limit is exhausted with unresolved Important findings: stop
  automatic iteration and request an explicit user decision rather than
  continuing until the agent step limit.
- No observed verification proof is available: identify the command or proof
  as unobserved and do not claim it passed.
- A reviewer attempts to edit repository files: preserve edit-denied behavior;
  reviewers remain read-only and fixes remain outside reviewer actions.

## Dependencies & Constraints

- Preserve sequential safety: run `review-spec` first, and run
  `review-quality` only after a fresh spec PASS.
- Preserve read-only reviewers and ad-hoc `/review` as read-only and
  spec-first. Ad-hoc review may display requested severities but remains
  advisory.
- Optimize repeated remediation reviews only; the initial review remains
  complete.
- Do not add a database, service, plugin, MCP server, or generic workflow
  engine, and do not persist review state outside the implementation session
  without a concrete need established during planning.
- Prefer the smallest implementation compatible with existing Markdown skill,
  agent, command, test, and plan patterns. Follow YAGNI and avoid speculative
  abstractions.
- Do not change model assignments without a concrete planning reason and user
  approval.
- Do not reduce security, data-integrity, or initial extra-scope review
  coverage.

## Out of Scope

- Replacing review agents with external tools or services.
- Automatically fixing reviewer findings or removing user control over fix,
  appeal, accept-risk, and stop decisions.
- Running quality review before spec compliance.
- Broad repository linting unrelated to the implementation diff.
- Solving general model context-window limitations.
- Changing OpenCode itself.
- Modifying unrelated document workflows.

## Notes

The governing implementation context is primarily `skills/code-review/SKILL.md`,
`skills/spec-implement/SKILL.md`, `agents/review-spec.md`,
`agents/review-quality.md`, and `commands/review.md`, with related tests,
specifications, plans, planning-risk guidance, and README documentation.

The initial successful spec report should include `SPEC REVIEW: PASS`, review
ID, `Mode: initial`, met/total criteria, evidence groups, `Extra work: NONE`,
and a baseline fingerprint. Incremental success should identify its baseline
review, list changed paths, list only revalidated criteria, summarize carried
forward criteria by count, and state whether remediation has extra work.

The quality report should include `QUALITY REVIEW`, review ID, mode, status,
and grouped findings. Important findings are the only integrated blockers.
