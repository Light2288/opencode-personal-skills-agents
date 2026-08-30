# Plan: Multimodal Document Workflows

| Field           | Value                                      |
|-----------------|--------------------------------------------|
| **Title**       | Multimodal Document Workflows              |
| **Spec**        | specs/multimodal-document-workflows.md     |
| **Type**        | feature                                    |
| **Branch**      | feat/multimodal-document-workflows         |
| **Implementer** | spec-implementer                           |
| **Created**     | 2026-08-28 15:00:00                        |
| **Status**      | IMPLEMENTED                                |

## Context

This repository needs local conversion and storage of mixed text, PDF, image,
DOCX, XLSX, and PPTX sources into reusable evidence, followed by focused
Markdown workflows using the configured IBM ICA inference endpoint. The
implementation preserves `/analyze`, `doc-analyst`, and `/adr` boundaries and
reports lossy or failed extraction honestly.

No architecture map exists at `docs/architecture/map.md` for HEAD `b1237041b2a1d220a070037f7949752e69fe4315`; planning therefore used direct repository exploration. No Accepted or Proposed ADRs were found under `docs/adr/`.

Planning decisions:

- Use one new `document-worker` subagent, confined to `docs/evidence/**` and `docs/deliverables/**`; leave `doc-analyst` confined to `docs/analysis/**`.
- Keep conversion orchestration in the primary command agent. The worker receives normalized evidence, denies webfetch and shell, and performs inference through its configured IBM ICA model.
- Install checked-in conversion tooling with the rest of the global configuration so commands do not depend on the source repository path.
- Use `docs/evidence/<topic>/manifest.md`, `sources/<source-id>/`, and `intermediates/<source-id>/`. Markdown is the reusable evidence contract; extracted images and renderings are intermediates referenced by it, not deliverables.
- Use synthetic fixtures generated into an ignored temporary directory; commit the generator and assertions, not generated Office/PDF/image files.
- Replace all operational Haiku 4.5 declarations/routing in configuration, agents, commands, and skills with `ibm-ica/gpt-5.6-luna`; do not rewrite historical specs/plans outside this feature.

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. The branch
> name is `feat/multimodal-document-workflows`.
>
> Reference command (the implementer adapts to the detected base):
>
> ```bash
> git checkout <base> && git pull --ff-only && git checkout -b feat/multimodal-document-workflows
> ```
>
> If the repo is not a git workspace, branch creation is skipped and
> noted in the implementation report.

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Each task below maps to exactly one commit.

## Recommended Implementer

**Recommendation**: `spec-implementer`

The tasks are individually S/M, but local conversion fidelity, untrusted-document handling, scoped permissions, deterministic evidence, and partial-failure behavior require non-trivial security and data-integrity judgment. The full implementer is appropriate despite the absence of an L task.

Run with `/implement` for `spec-implementer`.

## Build & Test Commands

| Action | Command |
|--------|---------|
| Validate configuration | `python3 -m json.tool opencode.json >/dev/null && python3 -m unittest discover -s tests -p 'test_*.py'` |
| Check document dependencies | `python3 tools/document_ingest.py check-dependencies` |
| Generate synthetic fixtures | `python3 tests/fixtures/document_workflows/generate.py --output "$TMPDIR/opencode-document-fixtures"` |
| Install configuration | `./install.sh` |
| End-to-end smoke test | Restart OpenCode, then run `/ingest "$TMPDIR/opencode-document-fixtures" fixture-review` and the three deliverable commands against `docs/evidence/fixture-review/` |

The repository has no build step or existing automated test framework. Use Python standard-library `unittest` for repository validation; runtime Office parsing dependencies are tested separately.

## Tasks

### Task 1: Add configuration validation and synthetic fixtures `[M | risk: data]`

**Goal**: Establish test-first, non-confidential coverage for routing, permissions, installation, mixed-format normalization, and partial ingestion.

**Risk rationale**: Fixtures model client-document structures and must be demonstrably synthetic, generated outside tracked paths, and excluded from staging.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_configuration.py` | create | Validate JSON model fields, Markdown frontmatter, command-to-skill references, agent permissions, and install synchronization. |
| `tests/test_document_ingest.py` | create | Exercise deterministic discovery, source IDs, normalized Office content, coverage, and unreadable/legacy input behavior. |
| `tests/fixtures/document_workflows/generate.py` | create | Generate synthetic text, Markdown, PDF, image, DOCX with table/image, multi-sheet XLSX with formulas/chart, PPTX with notes/image, legacy placeholders, and an unreadable input. |
| `tests/fixtures/document_workflows/README.md` | create | Explain synthetic content, generation, expected coverage, and prohibition on committing generated files. |
| `.gitignore` | modify | Ignore generated fixtures, `docs/evidence/**`, `docs/deliverables/**`, conversion state, and local dependency environments without ignoring source tests or documentation. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `commands/analyze.md` | Existing command frontmatter and skill-routing shape. |
| `agents/doc-analyst.md` | Deny-first permission assertions and restricted tool controls. |
| `install.sh` | Existing synchronized-directory list as the source of install assertions. |

**Steps**:

1. Add standard-library tests that initially fail until the model declaration, new commands, skills, worker, tools synchronization, and deny-first permissions exist.
2. Generate all binary fixtures only under the explicit `--output` path; make generation refuse repository source paths unless explicitly safe and ensure fixture text states it is synthetic.
3. Cover mixed supported formats, embedded visuals, multiple XLSX sheets and formulas, a chart, PPTX notes and images, deterministic path sorting, unsupported `.doc/.xls/.ppt`, and one unreadable input.
4. Add ignore rules and a test that fails if generated evidence, deliverables, conversion output, or generated fixtures are tracked.

**Tests**:

- Run `python3 -m unittest discover -s tests -p 'test_*.py'`; retain expected failures until corresponding implementation tasks complete.
- Generate fixtures in `$TMPDIR` and confirm `git status --short` contains no generated binary or workflow artifact.

**Acceptance criteria covered**: Validation coverage; mixed-format and embedded-visual fixtures; multi-sheet XLSX; PPTX notes/images; unreadable input; no confidential or generated artifacts staged.

**Commit**: `test(documents): add synthetic workflow validation fixtures`

---

### Task 2: Correct Sol capabilities and migrate lightweight routing `[S | risk: none]`

**Goal**: Declare gpt-5.6-sol multimodal capabilities and replace operational Haiku 4.5 routing with `ibm-ica/gpt-5.6-luna`, while keeping `doc-analyst` on Sol.

**Risk rationale**: This is a bounded configuration correction with mechanically testable values.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `opencode.json` | modify | Set `attachment: true` and the required input/output modalities for `gpt-5.6-sol`. |
| `agents/spec-definer.md` | modify | Route the lightweight spec definer to `ibm-ica/gpt-5.6-luna`. |
| `agents/spec-implementer-lite.md` | modify | Route the lite implementer to `ibm-ica/gpt-5.6-luna`. |
| `agents/review-spec.md` | modify | Route the spec reviewer to `ibm-ica/gpt-5.6-luna`. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `opencode.json` | Existing IBM ICA provider and model declaration. |
| `agents/doc-analyst.md` | Existing `ibm-ica/gpt-5.6-sol` assignment, which remains unchanged. |

**Steps**:

1. Correct the attachment and modalities values for `gpt-5.6-sol`.
2. Declare `gpt-5.6-luna` and route `small_model`, explore, general, title, summary, spec-definer, spec-implementer-lite, and review-spec to `ibm-ica/gpt-5.6-luna`.
3. Remove operational Haiku 4.5 declarations/usages while retaining historical references in unrelated specs/plans.
4. Confirm `doc-analyst` remains on `ibm-ica/gpt-5.6-sol` and unrelated provider settings remain unchanged.

**Tests**:

- Run `python3 -m json.tool opencode.json >/dev/null`.
- Run the model and agent assertions in `tests/test_configuration.py`.

**Acceptance criteria covered**: Correct gpt-5.6-sol multimodal declaration; operational Luna routing; doc-analyst remains on gpt-5.6-sol.

**Commit**: `fix(config): declare gpt-5.6-sol multimodal inputs`

---

### Task 3: Implement the local Office normalization tool `[M | risk: data]`

**Goal**: Provide one narrowly scoped checked-in CLI that discovers inputs and normalizes DOCX, XLSX, and PPTX content and visuals without modifying sources.

**Risk rationale**: Conversion can omit, mislocate, or overwrite source data; deterministic output, read-only source handling, and explicit lossy coverage are central data-integrity risks.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tools/document_ingest.py` | create | CLI for dependency checks, deterministic discovery, source IDs, format-specific extraction, rendering, and machine-readable extraction reports. |
| `tools/requirements-document.txt` | create | Pin the minimal Python parsing dependencies for DOCX, XLSX, PPTX, and fixture image handling. |
| `tools/README.md` | create | Document the local Python and LibreOffice dependency split and supported/lossy behavior. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/doc-analyze/SKILL.md` | Lexicographically sorted normalized paths and stable `S1`, `S2` assignment. |
| `AGENTS.md` | Explicit errors, no silent catches, YAGNI, and no speculative wrappers. |

**Steps**:

1. Expose only `check-dependencies` and `normalize <local-folder> --output <evidence-intermediates>` operations; validate that the source is a local directory and that output is outside it.
2. Discover recursively, normalize relative paths, sort deterministically, assign `S1...`, classify supported and legacy formats, and emit a structured report consumed by `/ingest`.
3. Parse DOCX paragraphs, tables, sections where reliable, relationships, and embedded images; optionally render with headless LibreOffice to PDF for layout/visual coverage.
4. Parse XLSX visible values, formulas, sheet names, tables, dimensions/ranges, visibility/filter metadata, and embedded chart/drawing relationships; also render sheets/charts where LibreOffice is available, but never use rendering as the only spreadsheet representation.
5. Parse PPTX slides in order, visible text, notes, relationships, and embedded images/charts; render to PDF or slide images for visual/layout evidence.
6. Pass PDF and common image files through as direct model inputs; normalize text and Markdown without conversion.
7. Record method, extracted locations, skipped elements, warnings, and per-source COMPLETE/PARTIAL/FAILED status. Continue after per-source failures and exit nonzero only when the invocation itself cannot produce a usable report.
8. Never install dependencies, follow links outside the source root, execute document content/macros, overwrite sources, or emit document text to logs.
9. Before rendering, scan OOXML relationships and skip LibreOffice for any external relationship; preserve structured extraction as PARTIAL.
10. Bound direct text/Markdown at 10 MiB and direct PDF/image attachments at 100 MiB before reading or copying.
11. Treat `presentation.xml` slide relationships as authoritative; use filename fallback only when that part is absent.
12. Preserve declared PPTX ordinals and include only notes/media/charts reachable from resolved declared slides.
13. Process XLSX absolute anchors with worksheet ownership and safe position/extent, warning without cell-range invention when unresolved.

**Tests**:

- Run `tests/test_document_ingest.py` against generated fixtures, including stable IDs across repeated runs and PARTIAL status for unsupported/unreadable inputs.
- Verify source hashes and mtimes remain unchanged and all output stays below the requested output root.
- Run `python3 tools/document_ingest.py check-dependencies` with available and intentionally missing optional tools to verify actionable diagnostics.

**Acceptance criteria covered**: Supported discovery; legacy Office diagnostics; DOCX text/tables/visuals; XLSX sheets/values/formulas/tables/charts; PPTX order/text/visuals/notes; direct PDF/image handling; stable IDs; extraction methods and locations; PARTIAL continuation; source and intermediate safety; dependency diagnostics.

**Commit**: `feat(ingest): add local document normalization tool`

---

### Task 4: Add the document-worker permission boundary `[S | risk: security]`

**Goal**: Add one restricted worker for evidence and deliverable writing while preserving the existing `doc-analyst` boundary.

**Risk rationale**: The worker processes untrusted client documents; shell, network, delegation, and write permissions must be deny-first and narrowly scoped.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `agents/document-worker.md` | create | Worker instructions, gpt-5.6-sol assignment, prompt-injection boundary, and scoped writes. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `agents/doc-analyst.md` | Local-only subagent structure, deterministic temperature, `webfetch`/`bash`/`task` denial, and deny-first edit rules. |
| `agents/spec-planner.md` | Multiple allowed output roots using root-relative and nested-workspace permission patterns. |

**Steps**:

1. Keep `doc-analyst.md` unchanged and assign the new worker to `ibm-ica/gpt-5.6-sol`.
2. Allow reads needed for supplied evidence and writes only under `docs/evidence/**`, `**/docs/evidence/**`, `docs/deliverables/**`, and `**/docs/deliverables/**` after a global edit denial.
3. Deny bash, webfetch, and task delegation. State that inference uses the configured IBM ICA endpoint, document instructions are data, and confidential use requires endpoint approval.

**Tests**:

- Assert exact allow/deny frontmatter in `tests/test_configuration.py`.
- Attempt representative allowed evidence/deliverable writes and denied analysis/source/unrelated writes in an OpenCode smoke test.

**Acceptance criteria covered**: Local-only processing; no web access; narrow writes; read-only sources; prompt-injection resistance; no unrelated copying or unnecessary confidential logging.

**Commit**: `feat(agents): add scoped document worker`

---

### Task 5: Add reusable multimodal ingestion workflow `[M | risk: security]`

**Goal**: Implement `/ingest <local-folder> [topic]` as the orchestration and evidence layer over the normalization tool.

**Risk rationale**: The workflow hands untrusted extracted text and visuals to a model; it must prevent embedded instructions from changing behavior while preserving traceability and partial results.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/doc-ingest/SKILL.md` | create | Validation, dependency checks, normalization invocation, multimodal evidence analysis, manifest schema, overwrite gate, and coverage rules. |
| `commands/ingest.md` | create | Thin `/ingest` route through the primary build agent to the skill. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/doc-analyze/SKILL.md` | Discovery/source registry conventions, COMPLETE/PARTIAL semantics, citations, issue categories, and direct-evidence/inference distinction. |
| `commands/analyze.md` | Command frontmatter and `$ARGUMENTS` handoff pattern. |
| `agents/document-worker.md` | Evidence-writing boundary after primary-agent conversion. |

**Steps**:

1. Parse folder/topic, reject non-local or non-directory inputs, derive a safe topic when omitted, and check `docs/evidence/<topic>/` before any work; ask before updating and never silently overwrite.
2. Check dependencies before conversion. Give exact installation commands for missing required components and identify optional rendering degradation without installing anything.
3. Have the primary agent invoke only the installed `document_ingest.py normalize` command, with source and evidence-intermediate roots explicitly quoted and separated.
4. Delegate normalized text, direct PDF/image/render attachments, and extraction report to `document-worker`; explicitly frame all source content as untrusted evidence.
5. Produce `manifest.md` plus per-source normalized evidence under `sources/S<n>/`, keeping renderings and extracted assets under `intermediates/S<n>/`.
6. Record the source registry, methods, source/location citations, coverage, skipped/lossy content, findings (requirements, constraints, assumptions, decisions, risks, contradictions, ambiguities, gaps, open questions), and direct evidence versus inference.
7. Mark the set PARTIAL whenever any discovered source or required representation fails; preserve all readable-source results.

**Tests**:

- Smoke-test `/ingest` with generated fixtures and inspect deterministic registry, citations, visual findings, input issues, and COMPLETE/PARTIAL status.
- Test collision refusal/update prompt, missing dependency diagnostics, invalid folder, malicious in-document instructions, and no output outside the topic directory.

**Acceptance criteria covered**: Full `/ingest` workflow; manifest; citations; evidence categories; reusable evidence location; visual/text extraction; COMPLETE/PARTIAL; collision handling; untrusted-input behavior.

**Commit**: `feat(ingest): add multimodal evidence workflow`

---

### Task 6: Integrate reusable evidence with analyze `[S | risk: none]`

**Goal**: Define `/analyze` as a consumer of existing evidence or a delegator to ingestion for raw multimodal folders without replacing its analysis contract.

**Risk rationale**: This is a documented routing refinement that preserves established behavior and permissions.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/doc-analyze/SKILL.md` | modify | Detect evidence paths, explain raw-document delegation, and preserve existing analysis output and source conventions. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/doc-analyze/SKILL.md` | Existing analysis phases, output template, and `docs/analysis/**` target. |
| `agents/doc-analyst.md` | Existing unchanged analysis-only permission fence. |

**Steps**:

1. Document that `/ingest` owns normalization and reusable evidence, while `/analyze` owns requirement/contradiction/gap analysis output.
2. When given `docs/evidence/<topic>/`, analyze its manifest and normalized sources without reconversion.
3. When given a raw folder containing Office/PDF/image inputs, instruct the primary workflow to run shared ingestion first and then analyze the resulting evidence; do not duplicate conversion logic in `doc-analyze`.
4. Preserve existing text/Markdown analysis behavior and output collision handling.

**Tests**:

- Validate existing `/analyze` routing and output path remain unchanged.
- Smoke-test analysis of an evidence directory and raw-folder delegation without duplicated normalization.

**Acceptance criteria covered**: Clear `/ingest`–`/analyze` relationship; evidence reuse; existing `/analyze` remains usable.

**Commit**: `feat(analyze): consume reusable document evidence`

---

### Task 7: Add source-faithful summary workflows `[M | risk: data]`

**Goal**: Produce cited meeting, executive, technical, and general Markdown summaries from an evidence set.

**Risk rationale**: Client-facing summaries can misstate unsupported facts, owners, dates, impacts, or recommendations; fidelity and omission rules are data-integrity concerns.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/doc-summarize/SKILL.md` | create | Evidence validation, four templates, citation/fact/inference rules, naming, and overwrite gate. |
| `commands/summarize.md` | create | Thin `/summarize` route to the skill. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/doc-analyze/SKILL.md` | Source citation and inference-labeling conventions. |
| `agents/document-worker.md` | Scoped `docs/deliverables/**` writer and untrusted-evidence boundary. |

**Steps**:

1. Validate evidence path, summary type, optional topic, and evidence coverage before delegation.
2. Define meeting, executive, technical, and general Markdown templates exactly around the spec fields.
3. Require citations for facts/source claims, label analyst inference, and omit or explicitly mark unsupported fields rather than filling them.
4. Write only to `docs/deliverables/summaries/` after collision confirmation and include evidence-set identity and coverage limitations.

**Tests**:

- Exercise all four templates with missing participants, owners, deadlines, recommendations, and ranges.
- Assert citations, fact/inference labels, Markdown-only output, path confinement, and collision prompts.

**Acceptance criteria covered**: All summary variants and fields; evidence citations; unsupported-field handling; output path; Markdown and overwrite safety.

**Commit**: `feat(summarize): add cited document summary workflows`

---

### Task 8: Add evidence-based estimation workflow `[M | risk: data]`

**Goal**: Produce traceable three-point estimates that separate source constraints from estimator assumptions.

**Risk rationale**: Unsupported scope or false precision can materially mislead client planning; provenance, ranges, and uncertainty must remain explicit.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/doc-estimate/SKILL.md` | create | Estimation process, template, citation rules, uncertainty handling, naming, and overwrite gate. |
| `commands/estimate.md` | create | Thin `/estimate` route to the skill. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/doc-analyze/SKILL.md` | Evidence and inference provenance conventions. |
| `agents/document-worker.md` | Scoped deliverable write boundary. |

**Steps**:

1. Validate evidence scope and optional topic, and carry forward PARTIAL coverage limitations.
2. Define scope/exclusions, assumptions/open questions, work breakdown, explicit unit/team model, optimistic/likely/pessimistic ranges, confidence, dependencies, risks, contingency rationale, and timeline implications.
3. Cite evidence-derived scope and constraints; label estimator assumptions and avoid unjustified granular values or deterministic commitments.
4. State which missing information could materially change ranges and write only to `docs/deliverables/estimates/` after collision confirmation.

**Tests**:

- Test sparse and partial evidence, unsupported team assumptions, missing scope, range ordering, confidence rationale, and change drivers.
- Assert citations, assumption labels, Markdown-only output, path confinement, and collision prompts.

**Acceptance criteria covered**: Estimate scope/exclusions, work breakdown, three-point ranges, units/team assumptions, confidence, risks/dependencies/contingency/timeline, citations, no false precision, change drivers, output safety.

**Commit**: `feat(estimate): add evidence-based estimation workflow`

---

### Task 9: Add exploratory architecture comparison workflow `[M | risk: data]`

**Goal**: Produce cited, non-authoritative option comparisons that can inform but never create or accept an ADR.

**Risk rationale**: Unexplained scoring or accidental decision authority can turn uncertain evidence into a misleading architecture commitment.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `skills/arch-compare/SKILL.md` | create | Option analysis, matrix/scoring rules, sensitivity analysis, ADR status handling, naming, and overwrite gate. |
| `commands/compare.md` | create | Thin `/compare` route to the skill. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `skills/arch-design/SKILL.md` | MADR terminology, status semantics, decision drivers, and Accepted/Proposed distinction. |
| `commands/adr.md` | Existing authoritative `/adr` routing and user handoff. |
| `skills/doc-analyze/SKILL.md` | Citation and inference-labeling conventions. |

**Steps**:

1. Validate evidence path and comparison subject; identify explicitly included Accepted ADRs as binding and Proposed ADRs as advisory.
2. Capture options, drivers, mandatory constraints, costs, operational effects, risks, reversibility, and evidence gaps.
3. Use a decision matrix only when criteria support it; explain each weight and score and add sensitivity analysis when uncertainty or close totals could change ordering.
4. Recommend only when evidence supports a recommendation; otherwise report what would resolve the comparison and label unsupported judgments as assumptions.
5. State that the artifact is exploratory, never create/change an ADR, direct approval requests to `/adr`, and write only to `docs/deliverables/comparisons/` after collision confirmation.

**Tests**:

- Test no-recommendation evidence, close scores, uncertain weights, mandatory constraint failure, Accepted and Proposed ADR inputs, and absence of criteria suitable for scoring.
- Assert score explanations, sensitivity, citations, non-authoritative language, no ADR writes, Markdown output, and collision prompts.

**Acceptance criteria covered**: Traceable tradeoffs, optional explained matrix, sensitivity, supported recommendations, assumptions, ADR separation/status semantics, output safety; existing `/adr` remains authoritative.

**Commit**: `feat(architecture): add evidence-based option comparisons`

---

### Task 10: Install tools and document the workflows `[M | risk: security]`

**Goal**: Synchronize the new runtime files safely and document setup, formats, limitations, privacy, commands, and artifact hygiene.

**Risk rationale**: Installation controls which executable tooling and permission-bearing agent definitions become global; an incomplete or over-broad sync could break existing configuration or expose data.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `install.sh` | modify | Synchronize checked-in `tools/` without deleting unrelated user files and preserve existing agent/skill/command behavior. |
| `README.md` | modify | Document dependencies, installation/restart, commands, formats, locations, limitations, privacy, and cleanup/staging rules. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `install.sh` | Existing idempotent rsync/copy structure and base URL warning. |
| `README.md` | Existing installation and configuration documentation style. |

**Steps**:

1. Install the document CLI and dependency manifest to a deterministic OpenCode configuration path referenced by `doc-ingest`; do not broaden shell permissions or run package/system installation.
2. Ensure synchronization includes new agents, skills, and commands through existing directories and does not remove unrelated local OpenCode state.
3. Document Python package and LibreOffice installation commands by supported platform, required versus optional rendering capabilities, dependency checks, and restart steps.
4. Document `/ingest`, `/analyze` reuse, `/summarize`, `/estimate`, `/compare`, and `/adr`; supported/unsupported formats; evidence/deliverable paths; PARTIAL/lossy semantics; collision behavior; local conversion/storage versus IBM ICA inference; prompt-injection posture; cleanup and git hygiene.
5. Document that the unrelated `session_message.seq` error is not evidence of model incapability and is outside this feature.

**Tests**:

- Install into a temporary HOME/config root and run configuration tests against installed files.
- Run `./install.sh` twice to verify idempotence and confirm existing commands, skills, agents, and config remain present and valid.
- Confirm install performs no dependency installation and generated/runtime artifacts remain unstaged.

**Acceptance criteria covered**: README requirements; installation/restart; install synchronization; existing configuration validity; no staged sources/evidence/deliverables/conversion output; local dependency diagnostics and limitations.

**Commit**: `docs(documents): install and document local workflows`

---

### Task 11: Complete repository and end-to-end validation `[M | risk: other]`

**Goal**: Close the acceptance matrix with installed-config, mixed-format, permission, overwrite, and workflow smoke tests.

**Risk rationale**: OpenCode currently has no end-to-end test harness, and the known unrelated database error may block live invocation; validation must distinguish environment blockage from implementation failure and model capability.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `tests/test_configuration.py` | modify | Add final installed-tree and synchronization assertions discovered during integration. |
| `tests/test_document_ingest.py` | modify | Add final regression cases for conversion and coverage behavior. |
| `tests/README.md` | create | Record deterministic automated checks, live smoke procedure, artifact cleanup, and known environment blocker handling. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `install.sh` | Installed-tree validation target. |
| `tests/fixtures/document_workflows/generate.py` | Synthetic end-to-end input corpus. |
| `commands/analyze.md` and `commands/adr.md` | Regression targets for existing workflow usability. |

**Steps**:

1. Run JSON, frontmatter, routing, model, permission, dependency, install-sync, deterministic-ID, source-integrity, and git-hygiene checks.
2. Install to an isolated config root, restart/use OpenCode against it, ingest the synthetic corpus, and inspect manifest, normalized sources, visuals, citations, input issues, and PARTIAL status.
3. Generate all four summaries, an estimate, and a comparison; verify Markdown paths, provenance, uncertainty behavior, and collision confirmation.
4. Regression-test `/analyze` and `/adr` routing and ensure `/compare` neither creates nor accepts an ADR.
5. If `NOT NULL constraint failed: session_message.seq` blocks live invocation, record that exact environmental blocker, retain all lower-level validation results, and do not reinterpret it as a model or workflow failure.
6. Remove generated evidence, deliverables, intermediates, temporary fixtures, and isolated install state; confirm none are staged.

**Tests**:

- Run every command in Build & Test Commands.
- Compare source hashes before/after conversion and inspect `git status --short` for only intended configuration, skill, command, tool, test, and documentation files.

**Acceptance criteria covered**: Repository validation; full fixture coverage; all Markdown workflows; source immutability; collision handling; permission boundaries; existing workflows/config remain valid; generated artifacts not staged.

**Commit**: `test(documents): verify multimodal workflows end to end`

---

**Task ordering**: Task 1 establishes failing validation. Task 2 is independent after Task 1. Task 3 must precede Task 5. Task 4 must precede Tasks 5 and 7–9. Task 5 precedes Task 6 and supplies evidence for Tasks 7–9; Tasks 6–9 can otherwise be implemented independently. Task 10 follows runtime files so installation and documentation are accurate. Task 11 is the final integration gate.

## Edge Cases & Error Handling

- Invalid, remote, missing, or non-directory source: reject before dependency checks or output creation (Tasks 3, 5).
- Existing evidence or deliverable target: ask whether to update; preserve existing content unless explicitly approved (Tasks 5, 7–9).
- `.doc`, `.xls`, or `.ppt`: register as unsupported input issues, continue readable sources, and mark PARTIAL (Tasks 3, 5).
- Missing Python parser or LibreOffice: provide concrete installation diagnostics, install nothing, and mark affected representations PARTIAL rather than fabricating them (Tasks 3, 5, 10).
- DOCX layout/page unavailable: cite section/paragraph/table/image identifiers; never invent page numbers (Tasks 3, 5).
- Wide, hidden, filtered, or formula-bearing XLSX: preserve structured sheet/range data and metadata in addition to optional rendering; disclose limitations (Tasks 3, 5).
- PPTX animations, unsupported diagrams, or unavailable rendering: retain visible text, notes, relationships, and extracted media; report visual gaps (Tasks 3, 5).
- Office external relationships: skip LibreOffice rendering without logging targets, preserve structured extraction, and mark PARTIAL (Task 3).
- PPTX orphan slide members: ignore them when `presentation.xml` exists; warn for unresolved declared slides (Task 3).
- PPTX ordinal gaps: retain each declared slide's original ordinal and exclude media/charts reachable only from orphan slides (Task 3).
- XLSX absolute anchors: retain worksheet ownership and absolute position/extent, or mark PARTIAL when unresolved without inventing ranges (Task 3).
- Oversized direct inputs: apply fixed 10 MiB text and 100 MiB attachment limits before reading/copying and continue other sources (Task 3).
- Scanned PDF without reliable text: use direct visual evidence, identify unavailable text, and do not claim OCR beyond observed model output (Task 5).
- Symlinks escaping the source root: skip and report them; never read unrelated local files (Task 3).
- Per-source conversion failure: keep successful sources and intermediates, record the exact issue, and mark the set PARTIAL (Tasks 3, 5).
- Embedded prompt injection: treat it as quoted source content and never alter tools, scope, destinations, or workflow instructions because of it (Tasks 4, 5, 7–9).
- Unsupported summary/estimate/comparison fields: omit or label them; never infer participants, ownership, dates, effort, scores, or recommendations without support (Tasks 7–9).
- Close option scores or uncertain weights: run sensitivity analysis and withhold a recommendation when ordering is unstable (Task 9).
- Known OpenCode `session_message.seq` failure: report it as an external validation blocker only if reproduced; preserve other results (Task 11).

## Verification

1. Confirm architecture context in the implementation report: architecture map missing at planned HEAD; no repository ADRs were applicable during planning.
2. Run `python3 -m json.tool opencode.json >/dev/null` and `python3 -m unittest discover -s tests -p 'test_*.py'`.
3. Run `python3 tools/document_ingest.py check-dependencies`; verify missing-tool output is actionable and no installation occurs.
4. Generate the synthetic corpus under `$TMPDIR`, run normalization twice, and compare normalized path/source-ID registries for determinism.
5. Compare hashes/mtimes of source fixtures before and after normalization; ensure outputs remain under the selected temporary/evidence root.
6. Install into an isolated OpenCode config root twice and verify frontmatter, command-to-skill routing, model settings, agent permissions, tool availability, and idempotent synchronization.
7. Restart OpenCode and run `/ingest`; inspect DOCX tables/visuals, XLSX sheets/formulas/tables/charts, PPTX order/notes/images, PDF/image visual evidence, citations, methods, issues, and PARTIAL coverage.
8. Run all `/summarize` variants, `/estimate`, and `/compare`; verify citations, inference labels, uncertainty, output paths, Markdown-only deliverables, and overwrite prompts.
9. Run `/analyze` against reusable evidence and confirm `/adr` remains authoritative and unchanged.
10. Test malicious document instructions and verify no web use, shell access by `document-worker`, unrelated reads/copies, out-of-scope writes, or source modification.
11. Remove runtime artifacts and inspect `git status --short`; no source documents, generated fixtures, evidence, deliverables, or conversion outputs may be staged.
