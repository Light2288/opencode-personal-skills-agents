---
name: arch-design
description: Use when the user invokes /adr, requests a MADR, or needs an architecture decision evaluated and recorded with explicit options and tradeoffs.
---

# Architecture Design

Turn an architectural choice into a user-approved MADR at
`docs/adr/NNNN-<slug>.md`.

## Phase 1 — Gather the Decision

Collect and confirm:

- scope and context;
- decision drivers and constraints;
- confirmation criteria;
- 2–3 explicit options;
- pros and cons for every option;
- the user's selected option and rationale.

Require at least two options. Keep the comparison to at most three unless the
user supplies a concrete reason for more. Ask focused questions for missing
information. Do not silently select an option or invent the user's rationale.

Search existing ADRs for related or superseded decisions. Accepted records are
binding context; Proposed records are non-binding. Surface conflicts before
drafting.

## Phase 2 — Allocate the Record

1. Create `docs/adr/` if absent.
2. Search `docs/adr/NNNN-*.md` and parse valid four-digit prefixes.
3. Use one greater than the maximum existing number. Start at `0001`; preserve
   gaps rather than filling them.
4. Derive a concise lowercase hyphenated slug from the decision title.
5. Check the full target path for a collision before writing. If it exists,
   ask for a different slug or reassess concurrent numbering.

## Phase 3 — Lifecycle and Evolution

New records start as `Proposed`. Promotion to `Accepted` requires explicit
user approval of that status change; never infer acceptance from draft
approval.

When a decision evolves, create a new ADR. It supersedes the latest applicable
record, links that immediate predecessor in metadata and Related Decisions,
and explains the change. If ADR 0003 supersedes 0001, the next revision
supersedes 0003. Do not retroactively edit 0001, rewrite prior records, or
backfill an ancestor's status.

## Phase 4 — Draft and Approve

Render the complete MADR below and present the decision, rationale, option
tradeoffs, negative consequences, status, filename, and any supersession link
for approval. Write only after approval. A later promotion from Proposed to
Accepted is a separate explicit approval.

## MADR Template

```markdown
# <Decision Title>

| Field | Value |
|-------|-------|
| Status | Proposed |
| Date | <YYYY-MM-DD> |
| Decision Owners | <people or team> |
| Supersedes | <immediate predecessor link or None> |

## Context

<Problem, scope, constraints, and why a decision is needed now.>

## Decision Drivers

- <driver>
- <driver>

## Considered Options

### Option 1: <Name>

<Description.>

#### Pros

- <advantage>

#### Cons

- <tradeoff or cost>

### Option 2: <Name>

<Description.>

#### Pros

- <advantage>

#### Cons

- <tradeoff or cost>

## Decision and Rationale

Chosen option: **<option>**.

<Why it best satisfies the drivers and why alternatives were rejected.>

## Consequences

### Positive Consequences

- <benefit>

### Negative Consequences

- <cost, limitation, or operational burden>

## Confirmation Criteria

- <observable evidence that confirms the decision works>

## Related Decisions

- <ADR link and relationship, or None>

## Links

- <specification, plan, architecture map, or supporting evidence>
```

Add a third option by repeating the option section only when it was genuinely
considered. Do not remove Pros, Cons, or either consequence subsection.

## Exit Conditions

Success requires an approved Proposed record with max-plus-one numbering, at
least two compared options, explicit rationale, positive and negative
consequences, confirmation criteria, and correct related-decision links.
