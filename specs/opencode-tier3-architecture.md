# Opencode Tier 3: Architecture Layer

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Opencode Tier 3: Architecture Layer                    |
| **Type**      | chore                                                  |
| **Scope**     | ~/.config/opencode/ (skills, agents, commands)         |
| **Created**   | 2026-08-26 19:45:00                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

Tiers 1 and 2 establish coherent spec workflows (define → plan → implement) and quality gates (review + debug). But they lack the architectural context layer — a way to map the codebase, analyze requirements documents, and capture architectural decisions. This leaves spec-plan and spec-implement flying blind on:

- **Missing architecture map**: No systematic view of modules, responsibilities, boundaries, and dependencies. Planner must re-read the codebase each time; explore agent redundantly re-scans.
- **Unanalyzed requirements**: Documents (PDFs, specs, standards) are ingested ad-hoc, contradictions remain hidden, and traceability is manual and inconsistent.
- **Unmapped decisions**: Architectural choices (data model, auth scheme, API contract) are made informally, not recorded, and future specs reinvent or violate earlier decisions.
- **Missing planning inputs**: spec-plan has no structured way to consider architecture shape before decomposing tasks. ADRs, when they exist, are not discovered or linked.

## Desired Outcome

After Tier 3 is complete:

1. **Architecture map skill** (`arch-map`):
   - Produces and maintains `docs/architecture/map.md` — a human-readable codebase snapshot.
   - Documents modules, entry points, data stores, external integrations, test topology, build/test commands.
   - Captures dependency boundaries (direction, acyclic checks where applicable).
   - Stamps generation time and HEAD SHA; spec-plan validates freshness during planning and falls back to explore agent if stale.
   - Invoked via `/map` command; supports `force` to regenerate from current HEAD.
   - On first invocation or with `force`, re-scans via explore agent; on subsequent invocations, validates and reuses if current.
   - Remains skill-only: the host agent writes the single fixed `docs/architecture/map.md` artifact, while explore performs read-only retrieval. A dedicated agent is required only when the workflow needs a permission fence or model the host agent lacks.

2. **Document analysis skill** (`doc-analyze`):
   - Ingests a folder of documents (PDF, Word, markdown, etc.) via the agent `doc-analyst` (read-only, webfetch off, edit docs/analysis/**).
   - Produces `docs/analysis/<topic>.md` extracting requirements, actors, non-functional requirements with numbers, constraints, contradictions, and gaps.
   - Traces all findings to source documents using stable citation IDs (S1, S2, etc.) with a Sources registry.
   - Optionally cross-references existing Accepted ADRs to flag architectural conflicts.
   - Handles partial input (corrupted files, password protection) gracefully; reports skipped inputs and marks analysis as partial.
   - Real value: contradiction and gap detection, not just summary.
   - Uses the same top reasoning model as `review-quality`; its dedicated agent supplies both the `docs/analysis/**` permission fence and reasoning capability the host agent may lack.

3. **Architecture design skill** (`arch-design`):
   - Produces decision records in MADR format at `docs/adr/NNNN-<slug>.md`.
   - Captures context, decision drivers, 2–3 explicit options with tradeoffs, decision, consequences (including negative).
   - Fills the "what shape" layer between spec (what to build) and plan (which files to change).
   - Invoked via `/adr` command; assigns sequential number from existing ADRs.
   - Output becomes input to spec-plan; optional insertion point between define and plan phases.
   - Status lifecycle: Proposed → Accepted; supersession/amendment rules for evolved decisions.

4. **Integrated architecture workflow**:
   - spec-plan Step 2 validates architecture map freshness; if current, reads it as context; if stale, uses explore agent and warns user.
   - spec-plan searches existing ADRs and recommends them if they materially constrain the spec. Flags unresolved architectural decisions if they would make planning speculative.
   - Spec-plan task risk tags include architecture-category risks (data/concurrency/security).

5. **Commands**: `/map`, `/analyze`, `/adr` registered in `~/.config/opencode/commands/`.

## Acceptance Criteria

- [ ] Create `~/.config/opencode/skills/arch-map/SKILL.md` (~120 lines): documents workflow, SHA stamping, freshness validation, fallback to explore agent, integration point with spec-plan.
- [ ] Create `~/.config/opencode/skills/doc-analyze/SKILL.md` (~150 lines): ingestion workflow, citation format, contradiction/gap detection, ADR cross-reference mode, partial input handling.
- [ ] Create `~/.config/opencode/skills/arch-design/SKILL.md` (~100 lines): MADR output format, sequential numbering, status lifecycle (Proposed → Accepted, supersession rules), invocation via `/adr`.
- [ ] Create `~/.config/opencode/agents/doc-analyst.md`: mode subagent, edit allow for `docs/analysis/**` only, webfetch off, read documents provided by user.
- [ ] Create `~/.config/opencode/commands/map.md`: routes to `arch-map` skill; supports `force` argument.
- [ ] Create `~/.config/opencode/commands/analyze.md`: routes to `doc-analyze` skill; accepts document folder path and optional topic name.
- [ ] Create `~/.config/opencode/commands/adr.md`: routes to `arch-design` skill; accepts scope/context and accepts user input for decision drivers and options.
- [ ] `docs/architecture/map.md` template includes: modules table (name, responsibility, entry points), dependency graph (direction, boundaries), data stores, external integrations, test topology, build/test commands, generation metadata (timestamp, HEAD SHA, generated-by marker).
- [ ] `docs/adr/NNNN-<slug>.md` template (MADR): status, context, decision drivers, options (≥2), pros/cons per option, decision & rationale, consequences (positive + negative), confirmation criteria, related decisions, links.
- [ ] Update `~/.config/opencode/skills/spec-plan/SKILL.md` Step 2:
   - Validate `docs/architecture/map.md` existence and SHA freshness against HEAD.
   - If current, read relevant sections as context.
   - If stale or missing, use explore agent and warn user; suggest `/map force`.
   - Search `docs/adr/*.md` by title and drivers; recommend if relevant to spec scope.
   - Flag if an unresolved architectural decision would make planning speculative; offer to create ADR first.
- [ ] Update task template in spec-plan to include risk field with categories: `none | security | data | concurrency | migrations | other`.
- [ ] Spec-plan plan template updated to display task risk alongside size: `### Task N: <title> [S/M/L | risk: <category>]`.
- [ ] Verify docs/architecture/ and docs/adr/ directories exist or are created on first `/map` and `/adr` commands.
- [ ] All config (commands, agents, skill integrations) is owned by Tier 3; no changes deferred to Tier 1.

## Edge Cases & Error Handling

- **Map staleness detection**: If HEAD SHA in `map.md` does not match current HEAD, or any referenced key path no longer exists, treat as stale. Do not refresh automatically during plan; warn and suggest `/map force`.
- **Map generation on missing docs/architecture/**: If directory doesn't exist, create it. If `map.md` doesn't exist, regenerate from HEAD.
- **Partial document analysis**: If a document is corrupted, password-protected, or unsupported, record in "Input Issues" section, continue analyzing readable documents, mark analysis as partial, and warn user that coverage may be incomplete.
- **Analysis overwrite collision**: If `docs/analysis/<topic>.md` already exists, ask user whether to update it or choose a different topic. Never silently overwrite.
- **Topic inference**: If user provides no topic name, infer one from the document set; if ambiguous, prompt user to choose. Keep inferred topics concise and descriptive (2–5 words, ~50 chars).
- **ADR numbering collision**: Sequential numbering may have gaps if ADRs are deleted. Use the next integer higher than the maximum existing ADR number, not sequential fill. Preserve gaps.
- **Supersession chain**: If ADR-0003 supersedes ADR-0001, and user later wants to revise ADR-0003, create ADR-0004 that supersedes ADR-0003. Link the chain in metadata but do not backfill ADR-0001's status retroactively.
- **Proposed vs. Accepted ADRs**: doc-analyze treats Accepted ADRs as authoritative; Proposed ADRs as non-binding context. Distinguish in the analysis.
- **Unresolved architectural decision during planning**: If spec-plan identifies a decision that is not covered by existing ADRs and would materially change the plan tasks or acceptance strategy, pause and ask user whether to create the ADR first. If user declines, record the recommendation and continue.

## Dependencies & Constraints

- **Tier 1 and 2 completion**: Tier 3 assumes Tier 1 (baseline config, AGENTS.md, explore agent) and Tier 2 (code-review, debug skills, spec-plan structure) are complete. Verify status before starting Tier 3 implementation.
- **Explore agent integration**: arch-map skill delegates codebase re-scans to explore agent; spec-plan integration assumes explore agent is available and can return compact digests. If unavailable, fall back to in-context glob/grep (document fallback behavior).
- **Document ingestion format**: doc-analyze must support local or user-provided PDF, Word (.docx, .doc if parseable), markdown, and plain text. External-source acquisition is separate: fetch with a suitably permitted agent, then provide the local file to doc-analyst. Other formats (spreadsheets, visio) are out of scope unless a standard library exists in the project.
- **MADR format**: arch-design outputs MADR (Markdown Architecture Decision Record) format, not Y-Statements or other ADR styles. No format selection yet (YAGNI).
- **Deterministic citation IDs**: doc-analyze assigns source IDs (S1, S2, etc.) deterministically by sorting normalized file paths, so regenerating analysis produces stable citations.
- **Read-only doc-analyst agent**: The agent can read documents and docs/adr/, but edit only `docs/analysis/**`. Cannot modify ADRs or consume resources outside its boundary.
- **No webfetch required**: doc-analyst runs with webfetch off; all documents must be local or user-provided. Avoid external API calls during analysis.
- **Agent creation rule**: create a dedicated agent when a workflow needs a permission fence or model the host agent lacks. This justifies `doc-analyst`; delegation or interactivity alone does not.

## Out of Scope

- **Tier 1 and 2**: Already complete; assume their workflows and governance are stable.
- **Codebase refactoring or reorganization**: Tier 3 documents architecture; it does not refactor code.
- **Executable architecture validation**: No runtime architecture checks, schema validation, or dependency cycle detection tools. Map is human-maintained and human-verified.
- **Automatic architecture violations**: Tier 3 does not enforce decisions; it records them. Enforcement (linting, compliance checks) is a future tier or external tool.
- **Multiple ADR formats**: Only MADR. No Y-Statements, Nygard, or other formats yet.
- **Persistent audit trail**: Reviews and analyses are ephemeral; no database of past versions or decision history beyond git commit history. No audit trail tool.
- **Integration with external systems**: No Jira, Confluence, wikis, or external documentation tools. Standalone markdown files only.
- **Auto-fixing documents or requirements**: Tier 3 reports contradictions and gaps; it does not resolve them. Resolution is manual.

## Notes

- **Slug**: Confirmed as `opencode-tier3-architecture`.
- **Directory structure** after Tier 3:
  - `~/.config/opencode/skills/arch-map/SKILL.md` (new)
  - `~/.config/opencode/skills/doc-analyze/SKILL.md` (new)
  - `~/.config/opencode/skills/arch-design/SKILL.md` (new)
  - `~/.config/opencode/agents/doc-analyst.md` (new)
  - `~/.config/opencode/commands/map.md` (new)
  - `~/.config/opencode/commands/analyze.md` (new)
  - `~/.config/opencode/commands/adr.md` (new)
  - Modified: `~/.config/opencode/skills/spec-plan/SKILL.md`
  - Created on first use: `docs/architecture/`, `docs/adr/`, `docs/analysis/`
- **Testing Tier 3**:
  - Run `/map` on a codebase; verify `docs/architecture/map.md` is created with SHA and key paths.
  - Run `/map` again; verify it skips regeneration if SHA matches HEAD.
  - Run `/map force`; verify it regenerates and updates SHA.
  - Run `/analyze docs/requirements` with a folder of PDFs; verify `docs/analysis/security-requirements.md` (or inferred topic) is created with citations and Sources section.
  - Run `/adr` to create a decision record; verify `docs/adr/0001-auth-model.md` (or next number) is created in MADR format.
  - Run spec-plan on a spec; verify it validates map SHA and recommends relevant ADRs.
  - Verify `spec-plan plan-example.md` shows risk field in task headers.
  - Introduce a contradiction between an Accepted ADR and a new requirement document; run `/analyze docs/updates` with architecture cross-reference enabled; verify contradiction is reported and flagged.
- **Token economy**: Architecture retrieval uses explore agent (Haiku) for map generation and spec-plan integration. doc-analyst uses the `review-quality` top reasoning tier because it is low-volume, high-stakes work whose missed contradictions create false confidence. ADR creation may require reasoning but is not invoked frequently.
- **Reference**: Tier 1 spec: `specs/opencode-tier1-fixes.md` (Status: IMPLEMENTED). Tier 2 spec: `specs/opencode-tier2-quality.md` (Status: IMPLEMENTED).

## Post-Implementation Amendments

- Status remains `IMPLEMENTED`. Corrected `doc-analyst` to use the
  `review-quality` model, retained its explicit no-webfetch security fence,
  separated external acquisition from analysis, and documented the skill-only
  `arch-map` write boundary and agent-creation rule.
