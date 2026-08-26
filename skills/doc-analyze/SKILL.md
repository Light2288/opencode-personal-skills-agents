---
name: doc-analyze
description: Use when the user invokes /analyze or asks to analyze a local document folder for requirements, contradictions, gaps, citations, or ADR conflicts.
---

# Document Analysis

Analyze local documents into a traceable report at
`docs/analysis/<topic>.md`. The value of this workflow is contradiction and gap
detection, not a prose-only summary.

## Inputs

- Required: local document-folder path.
- Optional: topic name.
- Optional: ADR cross-reference mode.

Ask for a missing folder. Verify it exists and is local before proceeding.
Never use `webfetch` or an external API.

External-source acquisition is a separate workflow: use a suitably permitted
primary agent or scout to fetch a source, save it locally, then provide that
file to `doc-analyst`. If URL-to-analysis becomes a frequent need, ask the user
before introducing a domain-allowlisted `webfetch`; never grant open webfetch
to the analyst.

## Phase 1 — Discover Sources

1. Discover readable PDF, Word (`.docx`, and `.doc` only when parseable),
   Markdown, and plain-text files beneath the supplied folder.
2. Record unsupported formats as input issues; do not add format-specific
   tooling.
3. Normalize paths relative to the workspace, normalize separators, and sort
   lexicographically.
4. Assign stable IDs in sorted order: `S1`, `S2`, and so on. IDs remain stable
   while normalized paths remain unchanged.
5. Preserve a source registry mapping each ID to its normalized path.

Local PDF attachments may be read by the configured PDF-capable analyst model.
Do not claim Word coverage when a file cannot be parsed by available local
reading support.

## Phase 2 — Resolve Output

If no topic is supplied, infer a concise, descriptive 2–5 word topic from the
document set and convert it to a filename-safe slug. If more than one topic is
plausible, ask the user to choose instead of guessing.

Set the target to `docs/analysis/<topic>.md`. If it exists, ask whether to
update it or choose a different topic. Never silently overwrite an analysis.
Create `docs/analysis/` only after the output is resolved.

## Phase 3 — Extract Evidence

Delegate to the `doc-analyst` subagent with:

- the sorted source registry;
- the exact target path;
- ADR cross-reference mode;
- the required output template below.

The subagent exists because this workflow needs a permission fence and a
reasoning model the host agent may lack: edits are confined to
`docs/analysis/**`, external access is denied, and cross-document
contradiction, gap, assumption, and traceability judgments use the same
top-tier model as `review-quality`.

Require these evidence classes:

- actors and their goals;
- functional requirements;
- non-functional requirements, preserving every stated number, unit, range,
  percentile, deadline, or threshold;
- constraints and assumptions;
- contradictions between sources;
- ambiguities and gaps that block implementation or acceptance;
- direct evidence versus analyst inference.

Every finding must cite one or more IDs such as `[S1]` or `[S1, S3]`. A
finding without a citation must be labeled as inference and cite the evidence
that motivated it.

## ADR Cross-Reference Mode

When enabled, inspect `docs/adr/*.md` and read each record's status and
decision. Accepted ADRs are authoritative architecture constraints. Proposed
ADRs are non-binding context and must be labeled advisory. Report material
conflicts in `ADR Conflicts`, linking the ADR path and relevant source IDs.
Do not treat Proposed records as requirements and do not modify ADRs.

## Partial Inputs

Handle each corrupted, password-protected, unsupported, or unparseable file
independently:

1. Continue analyzing readable sources.
2. Add the skipped normalized path and concrete reason to `Input Issues`.
3. Set overall status to `PARTIAL` and coverage to incomplete.
4. Warn that conclusions may omit evidence from skipped inputs.

If no input is readable, do not produce a substantive analysis. Report the
input issues and blocker without inventing findings.

## Output Template

```markdown
# <Topic> Analysis

## Analysis Metadata

| Field | Value |
|-------|-------|
| Status | COMPLETE or PARTIAL |
| Coverage | <readable count>/<discovered count> inputs |
| Generated At | <ISO-8601 timestamp> |
| ADR Cross-Reference | enabled or disabled |

## Actors

- **<Actor>** — <goal or responsibility>. [S1]

## Functional Requirements

- **FR-1**: <testable requirement>. [S1]

## Non-Functional Requirements

- **NFR-1**: <quantified requirement with number and unit>. [S2]

## Constraints and Assumptions

- **Constraint**: <constraint>. [S1]
- **Inference**: <assumption requiring validation>. [S1, S2]

## Contradictions

- **C-1**: <incompatible statements and impact>. [S1, S2]

## Ambiguities

- **A-1**: <unclear requirement and question>. [S1]

## Gaps

- **G-1**: <missing information and why it matters>. [S2]

## ADR Conflicts

- <Accepted conflict or Proposed advisory context, ADR link, impact>. [S1]

## Input Issues

- `<path>` — <corrupted/password-protected/unsupported/unparseable reason>.

## Sources

- **S1** — `<normalized/path>`
- **S2** — `<normalized/path>`
```

Omit `ADR Conflicts` only when cross-reference mode is disabled. Keep `Input
Issues` and state `None` when all discovered inputs are readable.

## Exit Conditions

Success requires a report under `docs/analysis/**`, deterministic source IDs,
source-linked findings, explicit gaps and contradictions, and honest coverage.
Report whether the result is complete or partial and list all skipped inputs.
