---
agent: build
description: Review a diff against acceptance criteria
---

Invoke the `code-review` skill in advisory, read-only mode using the pasted
diff and acceptance criteria. Run the edit-denied reviewers sequentially and
do not edit application files.

Construct a self-contained ad-hoc review envelope from the pasted diff,
changed-file list, criteria, requested severities, and any supplied verification
proof. Mark unavailable integrated spec/plan state explicitly as ad hoc. Reject
missing essentials rather than guessing. Preserve spec-first ordering: run
quality only after a fresh spec PASS for this envelope. The result remains
advisory, and reviewers never apply fixes.

Input:

$ARGUMENTS
