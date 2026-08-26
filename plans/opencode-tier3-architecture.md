# Plan: Opencode Tier 3: Architecture Layer

| Field | Value |
|-------|-------|
| **Title** | Opencode Tier 3: Architecture Layer |
| **Spec** | specs/opencode-tier3-architecture.md |
| **Type** | chore |
| **Branch** | chore/opencode-tier3-architecture |
| **Implementer** | spec-implementer |
| **Created** | 2026-08-26 19:01:05 |
| **Status** | IMPLEMENTED |

## Context

The existing define, plan, implement, review, and debug workflows lack reusable architectural context, requirements analysis, and durable decision records. This change adds architecture mapping, local-document analysis, MADR creation, and command entry points, then integrates current maps and relevant ADRs into planning without adding executable architecture enforcement or external services.

Tier 1 and Tier 2 are verified as `IMPLEMENTED` in `specs/opencode-tier1-fixes.md` and `specs/opencode-tier2-quality.md`. The repository mirrors the global `~/.config/opencode/` layout through its top-level `skills/`, `agents/`, and `command/` directories.

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. The branch
> name is `chore/opencode-tier3-architecture`.
>
> Reference command:
>
> ```bash
> git checkout main && git pull --ff-only && git checkout -b chore/opencode-tier3-architecture
> ```
>
> The currently detected base is `main`. If the repo is not a git
> workspace, branch creation is skipped and noted in the implementation
> report.

Branch type mapping:

- feature → `feat/<slug>`
- bug → `fix/<slug>`
- refactor → `refactor/<slug>`
- chore → `chore/<slug>`

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Each task in the Tasks section maps to exactly one commit.

## Recommended Implementer

**Recommendation**: `spec-implementer`

Although all tasks are S or M and primarily change Markdown configuration, the path-confined write permission, mixed document ingestion behavior, architecture freshness rules, and unresolved-decision planning gate require non-trivial judgment. Use `/implement`; the lite implementer would be a poor fit for these permission and workflow semantics.

## Build & Test Commands

| Action | Command |
|--------|---------|
| Validate JSON | `python -m json.tool opencode.json` |
| Validate discovery | `opencode run "list agents, skills, and commands"` |

This repository has no package manifest, build step, or automated test framework. Validation therefore combines the discovery command with the manual workflow checks in Verification. Because opencode loads configuration only at startup, restart it before exercising newly created agents, skills, or commands.

## Tasks

### Task 1: Add architecture map skill `[M | risk: none]`

**Goal**: Add a skill that creates, validates, reuses, and force-regenerates a grounded architecture map for the current repository.

**Risk rationale**: The task documents repository inspection and Markdown generation; it does not affect a sensitive runtime domain.

**Write-boundary decision**: Keep `arch-map` skill-only. The host agent already has the required write permission and writes one fixed artifact, `docs/architecture/map.md`; the workflow does not ingest untrusted document instructions. Explore delegation is read-only repository retrieval and is irrelevant to this decision. A separate agent is warranted when the workflow needs a permission fence or model the host agent lacks, neither of which applies here.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/arch-map/SKILL.md` | create | Define map freshness, exploration, generation, and reuse workflows plus the map template |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-plan/SKILL.md` | Existing `task` delegation to the built-in `explore` agent and in-context `glob`/`grep`/`read` fallback |
| `skills/debug/SKILL.md` | Phased workflow and explicit exit-condition style |
| `opencode.json` | Existing `explore` override using `ibm-ica/claude-haiku-4-5` |
| `AGENTS.md` | YAGNI, convention matching, and epistemological-honesty rules |

**Steps**:

1. Create `skills/arch-map/SKILL.md` with valid `name: arch-map` frontmatter and a trigger-focused description covering `/map`, architecture mapping, and freshness checks.
2. Accept optional `force` input. Without `force`, read `docs/architecture/map.md` when present, parse its generation metadata, compare its stored HEAD SHA with `git rev-parse HEAD`, and verify that referenced key paths still exist.
3. Treat a missing map, mismatched SHA, or missing referenced key path as stale. Reuse a current map without rescanning; regenerate a stale or missing map on direct `/map` invocation, while reserving warning-only behavior during `spec-plan` for Task 5.
4. On first generation, create `docs/architecture/`. Delegate a single compact repository scan to `subagent_type: explore`, requesting modules, responsibilities, entry points, dependency direction and boundaries, data stores, integrations, tests, and manifest-derived commands. If delegation is unavailable, use in-context `glob`, `grep`, and `read` and disclose the fallback.
5. Define the exact `docs/architecture/map.md` template: generated timestamp, HEAD SHA, generated-by marker, modules table with responsibility and entry points, dependency graph/direction and boundaries, data stores, external integrations, test topology, and build/test commands.
6. Document that dependency information is descriptive and human-verified: report observed cycles where applicable, but do not introduce executable cycle checks or refactor the codebase.
7. Make `force` bypass reuse and regenerate from the current HEAD, replacing the map only after a complete scan result is available.

**Tests**:

- Inspect frontmatter and confirm the skill is discoverable with a concrete invocation description.
- Run `/map` in a repository without `docs/architecture/`; verify directory and map creation with every required section and metadata field.
- Run `/map` again at the same HEAD; verify the current map is reused without an explore rescan.
- Run `/map force`; verify regeneration and refreshed metadata.
- Change HEAD or remove a key referenced path; verify the existing map is classified stale.
- Simulate unavailable explore delegation and verify the documented in-context fallback reports that it was used.

**Acceptance criteria covered**: Create `arch-map`; include the complete map template; support SHA/path freshness, reuse, force regeneration, explore fallback, dependency boundaries, and first-use `docs/architecture/` creation.

**Commit**: `feat(arch-map): add architecture mapping workflow`

---

### Task 2: Add confined document analysis workflow `[M | risk: security]`

**Goal**: Add a document-analysis skill and a PDF-capable subagent that can inspect local inputs and write only traceable analysis reports under `docs/analysis/`.

**Risk rationale**: The subagent defines a security boundary: edits must be confined to `docs/analysis/**`, external fetching must be disabled, and source documents and ADRs must remain read-only.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `agents/doc-analyst.md` | create | Define the model, local-only tools, write confinement, and analysis responsibilities |
| `skills/doc-analyze/SKILL.md` | create | Define ingestion, citations, extraction, conflict/gap detection, output, and partial-input behavior |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `agents/review-spec.md` | Subagent frontmatter, explicit model pinning, deterministic temperature, and deny-by-default tool posture |
| `agents/spec-planner.md` | Ordered path-scoped `edit` permission map with broad deny rules before narrow allows |
| `agents/review-quality.md` | Reuse its top reasoning tier, `ibm-ica/gpt-5.6-sol`, for high-stakes contradiction, gap, assumption, and traceability analysis |
| `skills/code-review/SKILL.md` | Structured evidence/status reporting rather than unsupported summary |
| `AGENTS.md` | Explicit failures and honest reporting of incomplete evidence |

**Steps**:

1. Create `agents/doc-analyst.md` as a `subagent`, pin the same top reasoning model as `review-quality` (`model: ibm-ica/gpt-5.6-sol`), use deterministic temperature, allow local read/search, deny bash, task, question, and `webfetch`, and configure `edit` with broad deny rules followed by allows only for `docs/analysis/**` and its absolute-worktree equivalent. The agent exists because the workflow needs a permission fence and reasoning model the host agent may lack, not because delegation is intrinsically useful.
2. State in the agent body that it reads only user-provided local documents and `docs/adr/`, never modifies source documents or ADRs, never uses external APIs, and reports unreadable inputs rather than fabricating coverage.
3. Create `skills/doc-analyze/SKILL.md` with valid frontmatter and inputs for a document-folder path, optional topic, and optional ADR cross-reference mode.
4. Discover PDF, parseable Word, Markdown, and text inputs; normalize and sort paths before assigning deterministic `S1`, `S2`, and subsequent source IDs. Treat unsupported formats as input issues rather than adding format-specific tooling.
5. If no topic is supplied, infer a concise descriptive topic of 2–5 words. Ask the user only when inference is ambiguous. Before writing, detect `docs/analysis/<topic>.md`; ask whether to update it or choose another topic and never overwrite silently.
6. Create `docs/analysis/` on first use, delegate extraction to `doc-analyst`, and require actors, functional requirements, quantified non-functional requirements, constraints, assumptions, contradictions, ambiguities, and gaps. Prioritize contradiction and gap detection over prose summary.
7. Require each finding to cite one or more stable source IDs and define a Sources registry mapping each ID to its normalized path. Distinguish direct evidence from inference.
8. When ADR cross-reference is enabled, read statuses and decisions in `docs/adr/*.md`: treat Accepted records as authoritative and Proposed records as non-binding context, and report material conflicts with citations and ADR links.
9. Handle corrupted, password-protected, and unparseable documents per file: continue with readable inputs, list each skipped file and reason under `Input Issues`, label the overall analysis partial, and warn that coverage is incomplete.
10. Define the output template at `docs/analysis/<topic>.md`, including status/coverage metadata, actors, requirements, non-functional requirements, constraints, contradictions, gaps, optional ADR conflicts, input issues, and Sources.

**Tests**:

- Inspect agent frontmatter to verify its explicit PDF-capable model, `webfetch: deny`, denied execution/delegation, and last-match path-scoped edit allows.
- Validate that an attempted edit outside `docs/analysis/**` is denied while creation under that directory is permitted.
- Analyze a mixed local folder and verify deterministic source IDs, source-linked findings, actors, quantified NFRs, contradictions, and gaps.
- Include a corrupted or password-protected input; verify readable inputs still produce a report marked partial with an `Input Issues` entry.
- Omit the topic for both clear and ambiguous document sets; verify inference in the first case and a user prompt in the second.
- Pre-create the target analysis file; verify the workflow asks before updating or renaming it.
- Cross-reference one Accepted and one Proposed ADR; verify authoritative and advisory treatment differ and a contradictory Accepted decision is flagged.

**Acceptance criteria covered**: Create `doc-analyze` and `doc-analyst`; support local PDF/Word/Markdown/text ingestion, deterministic citations, source registry, contradiction/gap detection, optional ADR comparison, partial analysis, overwrite protection, topic inference, first-use directory creation, scoped edits, and disabled webfetch.

**Commit**: `feat(doc-analysis): add confined requirements analysis workflow`

---

### Task 3: Add MADR design skill `[M | risk: none]`

**Goal**: Add an interactive architecture-design skill that records decisions as sequentially numbered MADRs and preserves decision evolution.

**Risk rationale**: The task creates human-readable decision records and does not itself modify security, data, concurrency, or migration behavior.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/arch-design/SKILL.md` | create | Define ADR discovery, questioning, numbering, MADR rendering, lifecycle, and supersession |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-define/SKILL.md` | User-question workflow, concise slug handling, and approval-oriented drafting |
| `skills/spec-plan/SKILL.md` | Existing status-gated document workflow and structured Markdown templates |
| `AGENTS.md` | YAGNI and explicit tradeoff documentation |

**Steps**:

1. Create `skills/arch-design/SKILL.md` with valid `name: arch-design` frontmatter and triggers for `/adr`, MADR, and architecture decisions.
2. Gather scope/context, decision drivers, constraints, confirmation criteria, and at least two explicit options. Require pros and cons for each option and keep the workflow to 2–3 options unless the user provides a concrete reason for more.
3. Search `docs/adr/NNNN-*.md`; create `docs/adr/` when absent, parse existing numeric prefixes, and select one greater than the maximum. Start at `0001` and preserve gaps rather than filling them.
4. Derive a concise filename slug and detect collisions before writing `docs/adr/NNNN-<slug>.md`.
5. Define a MADR template containing status, context, decision drivers, considered options, per-option pros and cons, decision and rationale, positive and negative consequences, confirmation criteria, related decisions, and links.
6. Create new records as `Proposed`. Document promotion to `Accepted` as an explicit user-approved status change, and distinguish Accepted decisions from non-binding Proposed records.
7. For evolved decisions, create a new ADR that supersedes the latest applicable record, link the supersession chain in the new record and related-decision metadata, and do not retroactively rewrite older records or backfill an original ancestor's status.
8. Present the draft decision and tradeoffs for approval before writing the ADR; do not silently choose an option where the user has not made the decision.

**Tests**:

- Run `/adr` with no existing ADR directory; verify directory creation and a `0001-<slug>.md` Proposed record.
- Seed `0001` and `0003`; verify the next ADR is `0004`, not `0002`.
- Verify the generated MADR contains every required field, at least two options, pros/cons, rationale, and both positive and negative consequences.
- Exercise Proposed-to-Accepted promotion and verify it requires explicit approval.
- Create a supersession chain and verify each new ADR points to its immediate predecessor without retroactively changing the original ancestor.

**Acceptance criteria covered**: Create `arch-design`; provide the complete MADR template, max-plus-one numbering, Proposed/Accepted lifecycle, supersession rules, `/adr` integration behavior, and first-use `docs/adr/` creation.

**Commit**: `feat(arch-design): add MADR decision workflow`

---

### Task 4: Register architecture commands `[S | risk: none]`

**Goal**: Expose the three Tier 3 workflows through argument-aware `/map`, `/analyze`, and `/adr` commands.

**Risk rationale**: These are thin command prompts that route user input to the confined workflows defined in Tasks 1–3.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `command/map.md` | create | Load `arch-map` and pass optional `force` input |
| `command/analyze.md` | create | Load `doc-analyze` and pass folder/topic input |
| `command/adr.md` | create | Load `arch-design` and pass scope/context input |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `command/plan.md` | Minimal command frontmatter and prompt-body convention |
| `command/debug.md` | Existing standalone workflow command wording |
| `skills/arch-map/SKILL.md` | Canonical map workflow and `force` semantics |
| `skills/doc-analyze/SKILL.md` | Canonical folder/topic analysis workflow |
| `skills/arch-design/SKILL.md` | Canonical decision-gathering workflow |

**Steps**:

1. Create all three command files with concise descriptions and prompt bodies that explicitly tell the selected primary agent to load and follow the matching skill; do not set `agent:` to a skill name because command routing targets agents, not skills.
2. Include `$ARGUMENTS` in every command body so input is not discarded.
3. Make `/map` interpret an exact `force` argument as forced regeneration and otherwise validate/reuse normally.
4. Make `/analyze` pass the required document-folder path and optional topic to `doc-analyze`, allowing that skill to ask only for missing or ambiguous input.
5. Make `/adr` pass supplied scope/context and allow `arch-design` to collect drivers and options interactively.

**Tests**:

- Restart opencode and verify `map`, `analyze`, and `adr` appear in command discovery.
- Invoke each command with arguments and verify `$ARGUMENTS` reaches the corresponding skill workflow.
- Invoke `/map force` and verify forced regeneration is selected.
- Invoke `/analyze <folder> <topic>` and verify both values are retained.
- Invoke `/adr <context>` and verify the workflow continues by asking for missing drivers and options.

**Acceptance criteria covered**: Register `/map`, `/analyze`, and `/adr` with their specified arguments and skill routing.

**Commit**: `feat(commands): add architecture workflow commands`

---

### Task 5: Integrate architecture context into planning `[M | risk: none]`

**Goal**: Teach `spec-plan` to consume current architecture maps and relevant ADRs, while retaining delegated exploration and explicit user control when decisions are unresolved.

**Risk rationale**: The task changes planning instructions and risk vocabulary but does not implement any sensitive application behavior.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/spec-plan/SKILL.md` | modify | Add map validation, ADR discovery, decision gating, stale-map handling, and complete risk categories |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/spec-plan/SKILL.md` | Existing Step 2 explore delegation, clarification limit, plan template, review question, and risk rationale rules |
| `skills/arch-map/SKILL.md` | Canonical metadata fields and SHA/path freshness definition from Task 1 |
| `skills/arch-design/SKILL.md` | ADR statuses, decision-driver fields, and supersession semantics from Task 3 |
| `plans/opencode-tier2-quality.md` | Existing task risk header and rationale presentation |

**Steps**:

1. Extend Step 2 before delegated exploration to look for `docs/architecture/map.md`, parse the canonical metadata, compare its SHA with current HEAD, and verify referenced key paths.
2. If the map is current, read only sections relevant to the spec's scope and provide them as context to the explore agent so it can validate and supplement rather than repeat the entire scan.
3. If the map is missing or stale, do not refresh it automatically during planning. Warn the user, suggest `/map force`, and continue with the existing explore-agent scan; preserve the current in-context fallback when explore itself is unavailable.
4. Search `docs/adr/*.md` by title, context, decision drivers, and spec scope. Include materially constraining Accepted ADRs in plan context/reuse and identify Proposed ADRs as non-binding.
5. When no ADR resolves a decision that would materially change task decomposition or acceptance strategy, pause via `question` and offer to create an ADR first. If the user declines, record the recommendation and assumption in the plan, then continue without fabricating a decision.
6. Update the task-header template and Task Risk Tags section so the permitted categories exactly cover `none | security | data | concurrency | migrations | other`, while preserving one explicit risk value and rationale per task.
7. Update exploration guidance and review summaries to mention architecture-map freshness, applicable ADRs or unresolved decisions, and any `other` risk rationale without weakening existing S/M sizing or one-commit-per-task rules.

**Tests**:

- Plan with a current map and verify relevant map sections are consumed while explore validates/supplements them.
- Plan with a missing map, mismatched SHA, and missing referenced path; verify each case warns, suggests `/map force`, does not regenerate, and uses explore.
- Plan with a materially relevant Accepted ADR and verify it is linked and constrains task details; verify Proposed ADRs are labeled non-binding.
- Plan around a material unresolved decision; verify the workflow pauses, offers ADR creation, and records the recommendation if declined.
- Inspect the plan template and risk guidance to verify all six categories, including `other`, and the header format `### Task N: <title> [S/M/L | risk: <category>]`.
- Run a normal plan with no map or ADR directory and verify existing delegated-exploration behavior remains functional.

**Acceptance criteria covered**: Integrate map existence/SHA/path validation, current-map context, stale-map warnings and explore fallback, ADR search and recommendation, unresolved-decision handling, and the complete architecture-aware task risk format into `spec-plan`.

**Commit**: `feat(spec-plan): integrate architecture context`

**Task ordering**: Tasks 1–3 establish the independent skills and may be implemented in any order. Task 4 depends on Tasks 1–3 because its commands invoke those skills. Task 5 depends on Tasks 1 and 3 for canonical map metadata and ADR semantics. Each task is one commit; verification that spans commands occurs after all five commits.

## Edge Cases & Error Handling

- **Current SHA but deleted key path**: classify the map as stale even though the commit metadata matches (Tasks 1 and 5).
- **Missing map directory**: direct `/map` creates `docs/architecture/` and generates the map; `spec-plan` warns and explores but does not create it (Tasks 1 and 5).
- **Explore agent unavailable**: use in-context file discovery and disclose reduced delegation rather than aborting or inventing architecture (Tasks 1 and 5).
- **Analysis output collision**: ask whether to update the existing report or choose another topic; never overwrite silently (Task 2).
- **Unreadable input**: continue with readable documents, identify each skipped input, and mark the report partial (Task 2).
- **Moved document changes citation ordering**: regenerate IDs from normalized sorted paths and state that stability holds while paths remain unchanged (Task 2).
- **Accepted versus Proposed ADR**: treat only Accepted decisions as authoritative; present Proposed records as advisory context (Tasks 2 and 5).
- **ADR numbering gaps**: select maximum existing number plus one and preserve all gaps (Task 3).
- **Supersession chain**: supersede the immediate current decision with a new record and do not rewrite earlier ancestors (Task 3).
- **Unresolved planning decision**: pause only when the missing decision materially affects tasks or acceptance; if declined, document the assumption and proceed (Task 5).
- **Permission rule ordering**: place broad edit denials before narrow `docs/analysis/**` allows because opencode uses the last matching permission rule (Task 2).
- **Agent boundary rationale**: create a dedicated agent only when the workflow needs a permission fence or model the host agent lacks. `doc-analyst` needs both; `arch-map` remains skill-only because its host writes one fixed trusted artifact and explore performs read-only retrieval. (Tasks 1 and 2)
- **Config reload**: restart opencode after implementation before testing discovery or behavior (all tasks).

## Verification

1. Run `python -m json.tool opencode.json` and confirm the existing configuration remains valid.
2. Restart opencode, run `opencode run "list agents, skills, and commands"`, and verify `arch-map`, `doc-analyze`, `arch-design`, `doc-analyst`, `map`, `analyze`, and `adr` are discovered.
3. In a disposable repository without architecture docs, run `/map`; inspect `docs/architecture/map.md` for all required sections, timestamp, HEAD SHA, generated-by marker, and valid referenced paths.
4. Run `/map` again and then `/map force`; verify reuse followed by forced regeneration. Change HEAD or remove a referenced path and verify stale detection.
5. Run `/analyze docs/requirements` with readable and unreadable local inputs; verify deterministic citations, Sources, requirements, quantified NFRs, contradictions, gaps, input issues, and partial status.
6. Repeat analysis with an existing target file and with Accepted/Proposed ADRs; verify overwrite confirmation and correct ADR authority/conflict behavior.
7. Run `/adr` with no ADR directory, then with numbering gaps and a supersession case; verify MADR completeness, max-plus-one numbering, lifecycle, and links.
8. Run `/plan` against a spec with a current map and relevant ADR, then with a stale map and unresolved decision; verify context reuse, warning/fallback, ADR recommendation, and the decision gate.
9. Inspect a generated plan and confirm every task header uses `[S/M/L | risk: <none/security/data/concurrency/migrations/other>]`, every risk has a rationale, and every task maps to one Conventional Commit.
10. Confirm no runtime architecture enforcement, codebase refactor, external integration, alternate ADR format, or document auto-fix was introduced.

## Post-Implementation Amendments

- Kept Status `IMPLEMENTED` while correcting the `doc-analyst` model to the
  `review-quality` top tier, retaining explicit `webfetch: deny`, and clarifying
  local-only source acquisition.
- Recorded the `arch-map` skill-only write-boundary decision and corrected the
  agent-creation rationale to permission fencing or host-model capability.
