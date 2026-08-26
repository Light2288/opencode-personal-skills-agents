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

## Hard Rules

- Reviewers report findings only. They never edit files.
- Run `review-spec` before `review-quality`.
- Do not run quality review unless the current spec report is `PASS`.
- A missing reviewer is a blocking configuration error. Never skip it.
- A spec report becomes stale after any implementation or plan change.

## Step 1 — Validate Inputs and Reviewers

Require a readable diff and acceptance criteria. In integrated mode, read them
from the spec, plan, and repository. In ad-hoc mode, use the text supplied by
the user.

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

Launch `review-spec` with the diff and every acceptance criterion. Require it
to inspect both omissions and all changed work. It must cite criterion IDs or
exact criterion text and code locations.

The report has exactly one status:

```text
SPEC REVIEW: PASS
Criteria:
- <criterion>: MET — <location and evidence>
Extra work: NONE
```

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
5. After any change, discard prior reports and rerun `review-spec`.

In ad-hoc mode the report is advisory, but quality remains gated by spec-first
ordering. Return the non-PASS report without launching quality.

## Step 4 — Run Quality Review After PASS

Only after a fresh `PASS`, launch `review-quality` with the diff, relevant
files, `AGENTS.md`, and the spec report. Require judgment of:

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

Use this structure:

```text
QUALITY REVIEW
Summary: <concise judgment>
Findings:
- <Important|Minor|Nitpick> — <file:line>
  Issue: <evidence-based finding>
  Remedy: <specific minimal correction>
```

If there are no findings, state `Findings: NONE`. Never invent findings to
populate every severity.

## Step 5 — Return the Gate Result

In integrated mode, return both the fresh spec `PASS` report and the quality
report to `spec-implement`. The implementer or user decides whether to fix,
appeal, or accept quality findings. Reviewers never make that decision or
apply a remedy.

If quality changes are made, rerun `review-spec` before a new quality review;
the old spec pass and quality report are stale.

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

## Completion Conditions

The workflow completes only when one of these is returned:

- a non-PASS spec report, with quality not run;
- a fresh spec `PASS` plus a structured quality report;
- a named blocking reviewer configuration error.

Never claim both reports ran unless the spec report was `PASS` and the quality
reviewer actually returned a report.
