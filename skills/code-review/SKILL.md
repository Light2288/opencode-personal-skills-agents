---
name: code-review
description: Use for sequential acceptance-criteria and code-quality review. Runs review-spec first and review-quality only after spec compliance passes.
---

# Code Review

Review a diff without editing it. The gate accepts:

- the complete diff and changed-file list;
- the governing spec and acceptance criteria;
- the plan tasks, including size and risk tags;
- whether the call is integrated or ad hoc.

Every reviewer invocation receives a self-contained review envelope. It must
contain:

- review mode and review ID;
- governing spec path, exact spec slug, and governing plan path;
- spec fingerprint and plan fingerprint;
- diff base and current review fingerprint for the exact reviewed diff;
- complete changed-file list for the requested mode;
- stable acceptance criteria and affected criteria with impact reasons;
- previous spec result when criteria are carried forward;
- prior quality finding IDs and dispositions;
- whether the call is integrated or ad hoc; and
- observed verification commands and proof, or an explicit `unobserved` value.

The caller creates the envelope from current repository evidence; reviewers do
not depend on conversational memory. Use SHA-256 over the exact spec and plan
bytes. For the current review fingerprint, hash one canonical payload:
`review-diff-v1\0`, then the exact reviewed diff bytes, then `\0files\0`, then
the NUL-delimited sorted changed-file paths. The envelope identifies this
`review-diff-v1` representation. Capture the values as the immutable baseline
for the review. A later remediation receives a new current review fingerprint
without changing the accepted baseline values.

Keep the envelope, immutable baseline, reports, dispositions, and counters
session-local. Do not persist review state or add a state service, plugin,
database, framework, or agent.

## Hard Rules

- Reviewers report findings only. They never edit files.
- Run `review-spec` before `review-quality`.
- Do not run quality review unless the current spec report is `PASS`.
- A missing reviewer is a blocking configuration error. Never skip it.
- Remediation stales the current spec PASS but preserves the immutable baseline
  when its validation conditions still hold. A spec or plan change invalidates
  both the current PASS and immutable baseline and forces initial mode.
- Do not claim verification from an `unobserved` command; it must not be
  described as passing.

## Step 1 — Validate Inputs and Reviewers

Require a readable diff, acceptance criteria, and complete review envelope. In
integrated mode, read them from the spec, plan, and repository. In ad-hoc mode,
use the text supplied by the user and explicit ad-hoc markers for unavailable
integrated fields.

Validate the envelope before reading changed files. It is invalid when a
required field is missing, values are internally inconsistent, fingerprints
or the changed-file boundary are stale, the path/slug/fingerprint identifies
the wrong-spec, or the requested baseline cannot be established. Return:

```text
BLOCKED
Review ID: <id-or-unknown>
Error: <missing or inconsistent field and observed value>
Remedy: <minimal caller correction or full-initial fallback>
```

Do not reconstruct missing state from conversation or unrelated repository
files, guess a value, or switch to another spec. When an incremental baseline
or diff base is invalid but a complete feature diff can be established, the
caller must construct a new `initial` envelope; the reviewer must not silently
expand its own boundary.

Confirm that both `review-spec` and `review-quality` are available as
subagents. If either is unavailable, return:

```text
BLOCKED
Reviewer: <name>
Error: <configuration or discovery error>
Remedy: register the reviewer with its locked model and edit-deny permission
```

Do not silently substitute another agent or model.

## Step 2 — Run Spec Review

Assign descriptive criterion IDs before the first review. New specs and plans
should declare them explicitly. For a legacy document without IDs, derive a
deterministic ID from normalized criterion text, add a deterministic collision
suffix when needed, and retain that mapping for the session while the spec
fingerprint is unchanged. Do not rewrite legacy approved documents merely to
add IDs.

### Initial mode

`Mode: initial` is the first integrated review and every fallback review.
Launch `review-spec` with every acceptance criterion and the complete feature
diff. It must inspect omissions, every changed behavior, and extra scope. This
is unrestricted coverage: do not reduce security and data-integrity review or
any other existing coverage.

Successful initial output is concise:

```text
SPEC REVIEW: PASS
Review ID: <id>
Mode: initial
Criteria: <met>/<total> MET
Evidence groups:
- <group>: <locations>
Extra work: NONE
Baseline fingerprint: <fingerprint>
Current review fingerprint: <fingerprint>
Immutable baseline fingerprint: <fingerprint>
```

### Incremental mode

`Mode: incremental` is permitted after remediation only when the immutable
baseline spec review passed, the spec and plan fingerprints are unchanged, and
the remediation diff can be established exactly. Inspect that remediation
diff, not unchanged feature code.

Select affected criteria with explicit impact reasons. Revalidate criteria
mapped directly to changed files or behavior and criteria affected transitively
through a changed interface, permission boundary, data contract, error
contract, or output contract. Also revalidate any related prior MISSING or
EXTRA result. If impact is uncertain, revalidate; do not carry forward.

Carry forward a baseline-MET criterion only when the baseline spec review
passed and the envelope proves it is unaffected directly and transitively.
Always check the remediation diff for extra scope. If the fingerprints,
baseline, diff base, or impact proof are invalid, the caller must create a full
initial review envelope.

Successful incremental output is concise:

```text
SPEC REVIEW: PASS
Review ID: <id>
Mode: incremental
Baseline: <review-id>
Changed since baseline:
- <path>
Revalidated:
- <criterion-id>: MET — <evidence>
Carried forward: <count> unchanged criteria
Extra work in remediation: NONE
Current review fingerprint: <fingerprint>
Immutable baseline fingerprint: <fingerprint>
```

Do not restate unchanged criteria or plan tasks. For non-PASS results, include
detail only for affected criteria and MISSING or EXTRA findings.

Every spec report has exactly one status. Preserve these non-PASS forms:

```text
SPEC REVIEW: MISSING
Criteria:
- <criterion>: MISSING — <location or absent behavior and evidence>
Remedy: <specific requirement to satisfy>
```

```text
SPEC REVIEW: EXTRA
Extra work:
- <location>: <behavior outside the approved spec>
Why YAGNI: <boundary or criterion that excludes it>
Remedy: <remove it, or seek an approved spec/plan change>
```

Use `PASS` only when every criterion is met and no work lies outside the
approved boundary. If both missing and extra work exist, include both sections
under a non-PASS result; never hide one class of defect.

## Step 3 — Apply the Spec Gate

On `MISSING` or `EXTRA`:

1. Return the actionable spec report.
2. Do not launch `review-quality`.
3. In integrated mode, require the caller to ask the user whether to fix the
   code, fix the plan, or override the finding.
4. Wait for that decision; do not auto-fix.
5. After a spec or plan change, discard the baseline and use initial mode.
   After implementation remediation, use incremental mode only when its
   baseline rules are satisfied; otherwise use a full initial review.

In ad-hoc mode the report is advisory, but quality remains gated by spec-first
ordering. Return the non-PASS report without launching quality.

## Step 4 — Run Quality Review After PASS

Only after a fresh spec `PASS` for the same governing spec, fingerprints, and
reviewed state, launch `review-quality` with the envelope, relevant files,
`AGENTS.md`, and the spec report.

### Initial quality mode

`Mode: initial` performs one unrestricted review of the complete feature diff.
Require judgment of:

- readability;
- duplication;
- error handling, including silent or overly broad catches;
- coupling;
- naming.

Each finding must use one severity:

- `Important` — likely defect, unsafe behavior, serious maintainability cost,
  or violation that should block acceptance.
- `Minor` — concrete quality issue worth fixing but not a likely defect.
- `Nitpick` — small, optional polish with limited impact.

Findings are evidence-based and grouped by violated invariant or root cause.
Give each finding a stable finding ID that does not depend on a line number.
Each Important finding includes its severity, violated invariant, concrete
location, reachable input or execution path, concrete impact, why existing
validation does not catch it, significant variants checked, and one minimal
root-cause remedy. Return all known Important findings together, not one
example per shared invariant.

For archive-target invariants, when relevant, consider absolute paths, parent
traversal, normalized aliases, asset-root equality, duplicate resolved targets,
ancestor/descendant target collisions, duplicate archive members, and partial
writes before complete validation as variants of the shared root cause.

### Follow-up quality mode

`Mode: follow-up` runs only after an incremental spec PASS. Verify closure of
the prior accepted Important finding IDs and inspect the remediation diff for
Important regressions introduced by those fixes. Do not restart unrestricted
review across unchanged code, and do not introduce unrelated Minor or Nitpick
findings. A successful report names finding IDs verified as resolved and says
whether any Important remediation regression was found.

If a finding is equivalent to an earlier invariant/root cause, retain its
existing finding ID. Report uncertainty rather than merging unrelated issues.

In integrated mode, only unresolved `Important` findings block staging.
`Minor` and `Nitpick` are advisory and never automatically trigger remediation
or another review. Nitpick findings are hidden by default unless the user asks
for them. Do not report pure style preferences or pre-existing issues outside
the feature diff unless the feature introduces, touches, or materially worsens
them. Do not inflate severity.

Use this structure:

```text
QUALITY REVIEW
Review ID: <id>
Mode: initial|follow-up
Status: PASS|IMPORTANT_FINDINGS
Summary: <concise judgment>
Findings:
- <finding-id> — <Important|Minor|Nitpick> — <location>
  Invariant: <violated invariant>
  Path: <reachable execution or input path>
  Impact: <concrete impact and validation gap>
  Variants checked: <significant variants>
  Remedy: <minimal root-cause remedy>
```

If there are no findings, state `Findings: NONE`. Never invent findings to
populate every severity.

## Step 5 — Return the Gate Result

In integrated mode, return both the fresh spec `PASS` report and the quality
report to `spec-implement`. The implementer or user decides whether to fix,
appeal, or accept quality findings. Reviewers never make that decision or
apply a remedy.

Present all initial Important findings as one batch. The caller offers fix all,
select finding IDs, appeal findings, or accept documented risk. Reviewers do
not choose or apply dispositions.

If accepted quality changes are made, run incremental `review-spec` when its
baseline remains valid, then targeted follow-up quality. Otherwise fall back to
initial spec review. Never reuse a stale spec PASS.

## Step 5.5 Integration

`spec-implement` invokes this skill after full verification and before
staging according to planner-authored tags:

- mandatory for every L-sized task;
- mandatory for every M-sized task handled by the full implementer;
- mandatory for any task tagged `security`, `data`, `concurrency`, or
  `migrations`, regardless of size;
- optional, and explicitly offered to the user, only for S-sized tasks tagged
  `risk: none`;
- mandatory with a warning for a legacy task that omits risk; lite escalates
  that task to the full implementer.

Risk is read from the plan and never inferred during implementation. Any
listed sensitive domain makes review mandatory.

## Ad-Hoc `/review` Mode

Accept a pasted diff and acceptance criteria without a spec file. Run the same
spec-first sequence. The result is advisory and no files may be edited. A
non-PASS spec result still stops quality review because ordering is part of
the workflow, not merely the integrated enforcement policy.

Construct the envelope from the supplied diff, changed files, criteria,
requested severities, and verification proof. Use explicit ad-hoc markers for
unavailable integrated identity fields; ad-hoc mode does not require a
governing plan. It may display all requested severities, remains advisory, and
does not use integrated staging blockers or remediation counters.

## Completion Conditions

The workflow completes only when one of these is returned:

- a non-PASS spec report, with quality not run;
- a fresh spec `PASS` plus a structured quality report;
- a named blocking reviewer configuration error.

Never claim both reports ran unless the spec report was `PASS` and the quality
reviewer actually returned a report.
