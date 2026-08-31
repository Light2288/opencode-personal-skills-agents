---
name: repository-audit
description: Use for an evidence-based, read-only health assessment of pre-existing repository code, including clean worktrees.
---

# Repository Audit

Assess repository health without changing application files. This workflow is
separate from `code-review`: it works with a clean or dirty worktree, does not
require a diff or acceptance criteria, and inspects pre-existing code rather
than only changed lines.

## Hard Rules

- Remain advisory and read-only. The host and reviewer never edit, create,
  delete, stage, or commit application files and never automatically fix a
  finding.
- Use only the dedicated `review-audit` reviewer. If it is unavailable, return
  `BLOCKED`; do not substitute `review-spec` or `review-quality`.
- Do not persist findings or add a service, database, plugin, registry, or
  generic orchestration layer.
- Do not invoke an edit-capable implementation from the audit.

## 1. Establish Scope

Accept a clean or dirty Git worktree. A diff and acceptance criteria are
optional inputs, never prerequisites. Record dirty-worktree information as
attribution context, never the audit boundary.

Audit the whole repository by default. The user may instead provide an
optional directory or concern. Validate a supplied directory; if it is missing
or unreadable, report the limitation rather than silently broadening scope.

## 2. Inspect Instructions First

Before you inspect code, read project instructions and conventions, including
applicable `AGENTS.md` files, README guidance, manifests, configuration,
installation rules, and nearby test patterns. If instructions are unavailable
or unreadable, report the limitation and rely only on conventions that can be
verified.

## 3. Gather Evidence

Inspect pre-existing code in the selected scope. Assess, where applicable:

- correctness;
- security;
- data integrity;
- error handling;
- maintainability;
- duplication;
- coupling;
- naming;
- tests and test gaps;
- configuration; and
- documentation consistency.

Do not invent findings. A preference without concrete impact is not a defect.
If a precise location cannot be verified, cite the best repository reference
and state the limitation; otherwise omit the unsupported finding.

The host discovers available commands from project manifests and instructions.
When permitted, the host runs non-destructive tests and validation commands
and passes the exact command, exit result, and decisive output to the reviewer.
The reviewer has no shell access.

Report command evidence under two separate headings:

- **Observed verification**: commands actually run and their observed result,
  including failures.
- **Unobserved recommendations**: useful checks that were unavailable or not
  permitted and therefore not run.

Unobserved verification must not be described as passing. An unavailable or
not permitted command is a coverage limitation, not by itself a defect.

## 4. Review

Send `review-audit` a self-contained envelope containing selected scope and
concern, worktree state, instruction and convention evidence, files inspected,
observed verification, unobserved recommendations, and known limitations.

The reviewer reports concrete defects in severity order: Important, Minor,
then Nitpick. Optional improvements follow in a separate section and must not
be presented as defects.

Create each stable ID as `AUDIT-<token>` from normalized finding kind,
invariant or concern, path, and root-cause identity, not from a line number
alone. Equivalent findings retain the same identity when line numbers move.

Use this finding format:

```text
- AUDIT-<token> — <Important|Minor|Nitpick> — <File and line>
  Kind: Defect
  Evidence: <observed evidence>
  Impact: <concrete impact>
  Remedy: <minimal remedy>
```

Use the same fields with `Kind: Optional improvement` in the separate
`Optional improvements` section. When no concrete defect or improvement is
supported, report exactly:

```text
Findings: NONE
```

## 5. Selection and Handoff

Return the audit report without edits. If findings exist, ask the user to
explicitly select stable finding IDs for later implementation. Do not
auto-select findings.

For a selection, produce a self-contained handoff containing only selected
IDs, locations, evidence, impact, minimal remedies, verification observations,
and limitations. The handoff requires a separate spec and plan before an
edit-capable implementation phase. The audit ends after the handoff; it does
not call an implementer.
