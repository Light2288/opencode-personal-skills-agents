---
name: debug
description: Use for evidence-first investigation of unexpected test failures. Reproduce, isolate, name the root cause, then fix or escalate.
---

# Debug

Investigate unexpected failures without guessing.

## Hard Rule

Do not attempt a fix until the root cause is named with evidence. A plausible
hypothesis is not a root cause. Never weaken, skip, or delete a test to obtain
green output.

## Modes

- **Integrated**: called by `spec-implement` during Step 4b for an unexpected
  failure. Diagnosis may proceed to a regression test and minimal fix.
- **Standalone**: called by `/debug` with pasted output and no spec context.
  Investigate read-only and stop after naming the cause or escalating; do not
  edit application files or attempt a fix.

## Phase 1 — Reproduce

1. Record the exact command, environment facts relevant to the failure, exit
   code, and decisive output lines.
2. Run the smallest deterministic command that still produces the failure.
3. If it does not reproduce, report that fact and gather another observation;
   do not invent a cause from stale output.

Output a reproduction statement:

```text
REPRODUCED: <yes|no>
Command: <exact command>
Exit: <code>
Evidence: <decisive output>
```

## Phase 2 — Isolate

Use bisection or one controlled hypothesis test at a time. Change one variable
per cycle and compare the output. Keep a ledger of:

- hypothesis;
- command or controlled change;
- observed result;
- what the result rules in or rules out.

Stop after three bisection attempts or hypothesis cycles. Repeating the same
experiment does not reset the bound.

## Phase 3 — Name

State the root cause only when the observations establish a causal mechanism:

```text
ROOT CAUSE: <specific mechanism>
Evidence:
- <observation linking cause to failure>
- <control or bisection result excluding the nearest alternative>
```

If the cause cannot be named after three cycles, stop and escalate with the
reproduction record, all hypotheses tested, observations, and ruled-out
causes. Do not guess or continue implementation on an anonymous failure.

## Phase 4 — Regression Test and Fix

Integrated mode only:

1. Add a regression test that isolates the named cause.
2. Run it before production changes and confirm it fails for that cause.
3. Apply the minimum fix that addresses the named mechanism.
4. Run the regression test and affected suite to green.
5. Return control to `spec-implement` Step 4b.2 with the evidence and results.

Do not modify the test during green except to correct a genuine test mistake;
report any such correction.

## Exit Conditions

**Integrated success** requires all of:

- root cause named with evidence;
- a failing regression test added before the fix;
- minimal fix applied and relevant tests green.

**Standalone success** requires the root cause named with evidence. Return the
evidence so the user or implementer can decide what to change; make no edit.

**Escalation** occurs when the root cause remains unknown after three bounded
cycles. Return tested hypotheses and evidence, then wait. Never substitute a
speculative fix, suppress the failure, or weaken a test.
