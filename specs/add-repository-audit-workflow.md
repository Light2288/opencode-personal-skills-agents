# Add Repository Audit Workflow

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Add Repository Audit Workflow                          |
| **Type**      | feature                                                |
| **Scope**     | `/audit` command and skill, reviewer responsibilities, progress updates, contract tests, and README documentation |
| **Created**   | 2026-08-31 00:00:00                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

The existing `/review` workflow is intentionally strict: it requires a diff
and acceptance criteria and performs a read-only, spec-first review of changed
work. Users also need a way to assess the health of an entire repository,
including pre-existing defects, risks, test gaps, and worthwhile improvements,
even when the Git worktree is clean. A separate advisory workflow is needed so
that open-ended repository assessment does not weaken or conflate the existing
diff-based acceptance review.

Progress reporting also becomes repetitive during related exploration. Global
agent communication needs a concise, evidence-driven policy that avoids
repeating conclusions while still surfacing materially new information,
blockers, plan changes, and user decisions.

## Current Behavior

`/review` requires both a diff and acceptance criteria, so it cannot be used as
the dedicated workflow for auditing a clean repository or for assessing
pre-existing code outside the diff. The repository does not yet expose a
separate `/audit` command and skill with explicit whole-repository scope,
audit-specific reviewer permissions, or a finding-selection handoff to an
edit-capable implementation phase.

Progress updates can repeat related discoveries or conclusions instead of
combining them into one concise update.

## Desired Outcome

Add a separate `/audit` command and skill for an open-ended, read-only,
advisory repository health assessment. It must operate on clean and dirty
worktrees, default to the whole repository, and accept an optional
user-selected directory or concern. It must inspect project instructions and
conventions first, then examine pre-existing code rather than limiting review
to changed lines.

The audit should evaluate applicable concerns including correctness, security,
data integrity, error handling, maintainability, duplication, coupling,
naming, tests, configuration, and documentation consistency. It should run
available non-destructive tests and validation commands when permitted, and
clearly distinguish observed results from unobserved recommendations.

Audit reviewers must be read-only and edit-denied. Findings must be
evidence-based, ordered by severity, assigned stable IDs, and include file and
line references, impact, and minimal remedies. A clean assessment must report
`Findings: NONE`. Defects must be distinguished from optional improvements,
with no invented findings.

After reporting, the workflow should let the user select findings for a
separate edit-capable implementation phase. It must never automatically fix
findings, weaken `/review`'s diff/spec gate, or introduce unnecessary services,
persistence, plugins, or generic workflow frameworks.

Global progress behavior should issue at most one kickoff update for a related
exploration phase, avoid restating communicated conclusions, combine related
discoveries, continue silently without new information, and send later
updates only for materially new evidence, blockers, changed plans, or user
decisions. Final responses should not repeat progress conclusions and should
remain concise and factual across agents.

## Acceptance Criteria

- [ ] A `/audit` command and corresponding skill are defined and documented as a distinct, open-ended repository health assessment; `/review` remains a strict diff-based, spec-first, read-only acceptance review requiring a diff and acceptance criteria.
- [ ] The audit can run with either a clean or dirty Git worktree, requires neither a diff nor acceptance criteria, defaults to whole-repository scope, and supports an optional user-selected directory or concern.
- [ ] The audit inspects repository instructions and established conventions before reviewing code and assesses applicable correctness, security, data integrity, error handling, maintainability, duplication, coupling, naming, tests, configuration, and documentation consistency.
- [ ] The audit runs available non-destructive tests and validation commands when permitted, records observed command results separately from unobserved recommendations, and does not modify application files.
- [ ] Audit reviewers are read-only and edit-denied; the implementation explicitly evaluates whether a dedicated audit reviewer is required or an existing reviewer can be safely reused without conflating audit and diff-review responsibilities, choosing the smallest design that preserves clear responsibilities.
- [ ] Audit output reports evidence-based findings in severity order, gives each finding a stable ID, includes file and line references, impact, and a minimal remedy, distinguishes defects from optional improvements, and reports exactly `Findings: NONE` when no concrete issue is found.
- [ ] The workflow remains advisory, never automatically fixes findings, and after reporting allows the user to select findings for a separate edit-capable implementation phase.
- [ ] No unnecessary services, persistence, plugins, or generic workflow frameworks are added, and existing model assignments remain unchanged unless explicitly approved.
- [ ] Global progress-update behavior is specified and applied so related exploration has at most one kickoff update; later updates occur only for materially new evidence, a blocker, a changed plan, or a user decision; related discoveries are combined; redundant conclusions are not restated; and final responses do not repeat progress conclusions.
- [ ] Deterministic contract tests cover clean and dirty worktrees, optional scope, missing diff and acceptance criteria, instruction-first review, reviewer edit denial, command-result distinction, stable finding structure and severity ordering, `Findings: NONE`, no automatic fixes, finding selection handoff, `/review` gate preservation, and progress-update suppression/combination rules.
- [ ] README documentation concisely explains when to use `/audit` versus `/review`, the audit scope and advisory/read-only behavior, finding format, and the separate implementation handoff.

## Edge Cases & Error Handling

- Clean worktree: run the audit normally without requiring a diff or acceptance criteria.
- Dirty worktree: inspect the repository broadly while distinguishing pre-existing findings from worktree changes where evidence permits; do not silently narrow the audit to the diff.
- User-selected directory or concern: constrain or prioritize the assessment accordingly while preserving the documented audit contract.
- Missing or unreadable project instructions: report the limitation explicitly and continue only with conventions that can be verified.
- Validation command unavailable, disallowed, or failing: record the command and observed outcome (or inability to observe it); do not present unrun checks as passing or as discovered defects.
- No concrete issues found: emit `Findings: NONE` and do not manufacture optional improvements as defects.
- Finding without a precise source location: retain it only if evidence can be cited with the best available file/line or repository reference; otherwise omit it or report the limitation rather than inventing a location.
- User selects findings for implementation: pass only the selected findings to a separate edit-capable phase; do not edit files as part of auditing or auto-select findings.
- Existing `/review` invocation: preserve its current diff and acceptance-criteria gate and do not route it through the open-ended audit path.
- Repeated progress information: suppress it unless there is materially new evidence, a blocker, a changed plan, or a user decision.

## Dependencies & Constraints

The design must follow existing command, skill, agent, test, README, and
permission conventions in the repository. Audit execution and reviewers must
remain read-only with application-file edits denied. Tests and validation must
be non-destructive and respect project permissions. Finding identifiers and
output structure must be deterministic enough for contract tests. Do not
change existing model assignments without explicit approval. Keep the design
minimal and avoid new infrastructure or generalized workflow abstractions.

## Out of Scope

- Replacing, weakening, or broadening `/review` beyond its existing diff-based,
  spec-first acceptance-review contract.
- Automatically fixing, staging, committing, or otherwise editing application
  files during an audit.
- Building a persistent findings database, new service, plugin system, or
  generic workflow framework.
- Changing model assignments without explicit approval.
- Treating every optional improvement as a defect or requiring findings when
  no concrete issue is supported by evidence.

## Notes

The dedicated-reviewer decision should be recorded in the implementation as a
clear responsibility boundary: reuse is acceptable only if permissions,
inputs, output semantics, and review gates cannot be confused. The audit's
post-report selection is a handoff, not an implementation action performed by
the audit workflow.
