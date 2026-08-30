# Multimodal Document Workflows

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Multimodal Document Workflows                          |
| **Type**      | feature                                                |
| **Scope**     | OpenCode configuration, skills, and commands           |
| **Created**   | 2026-08-28 14:30:00                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

Client delivery work requires ingesting diverse document formats (text, Markdown, PDF, DOCX, XLSX, PPTX, images), extracting evidence with source citations, and producing focused deliverables (project estimations, architectural planning, summaries, comparisons, and decisions). Current OpenCode workflows do not support local multimodal document ingestion or generation of these specialized outputs from ingested evidence.

## Desired Outcome

OpenCode configuration extends with:

1. **Local multimodal ingestion** via `/ingest <folder> [topic]` that discovers supported formats, normalizes them locally (preserving textual and visual evidence with source locations), and produces reusable evidence under `docs/evidence/<topic>/`.

2. **Focused deliverable workflows**:
   - `/summarize <evidence-path> <template> [topic]` for meeting, executive, technical, and general summaries
   - `/estimate <evidence-path> [scope]` for effort estimation with ranges, assumptions, confidence, and risks
   - `/compare <evidence-path> <subject>` for option comparisons with tradeoffs and sensitivity analysis

3. **Architecture decision integration** where `/compare` may inform `/adr` but remains non-authoritative; existing approved ADRs are binding constraints.

4. **gpt-5.6-sol configuration corrected** to declare attachment support and text/image/PDF input modalities.

5. **Evidence reuse** across workflows with stable source IDs, manifest, and extraction coverage recorded.

Conversion, normalization, temporary files, and artifact storage remain local;
inference submits evidence and attachments to the configured IBM ICA endpoint.
Confidential use assumes that endpoint is approved for the material. Source
documents remain unchanged, and extracted content is untrusted evidence.

## Acceptance Criteria

### Model & Configuration
- [ ] gpt-5.6-sol is configured with `"attachment": true` and `"modalities": {"input": ["text", "image", "pdf"], "output": ["text"]}`
- [ ] doc-analyst remains assigned to gpt-5.6-sol
- [ ] Operational Haiku 4.5 model declarations and routing in `opencode.json`, agents, commands, and skills are replaced by `ibm-ica/gpt-5.6-luna`; historical specs/plans remain historical records
- [ ] Repository validation checks model configuration, command-to-skill routing, and permission boundaries

### Ingestion & Discovery
- [ ] `/ingest` discovers text, Markdown, PDF, DOCX, XLSX, PPTX, and common standalone image formats
- [ ] Legacy formats (DOC, XLS, PPT) are listed as unsupported input issues
- [ ] Recursive discovery with deterministic path normalization
- [ ] Stable source IDs assigned using existing S1, S2 pattern
- [ ] Source manifest produced and recorded

### Evidence Extraction & Citations
- [ ] DOCX text, tables, and embedded visuals represented in evidence
- [ ] XLSX sheets, values, relevant formulas, tables, and chart evidence represented with sheet/range citations
- [ ] PPTX visible content, visuals, slide order, and speaker notes represented with slide citations
- [ ] PDFs and images analyzed for textual and visual evidence
- [ ] Findings carry source and location citations (PDF page, PPTX slide, XLSX sheet/range, DOCX section/page, image ID) where available
- [ ] Direct evidence distinguished from analyst inference
- [ ] Extraction method and coverage recorded per source
- [ ] Failed or unsupported sources produce PARTIAL coverage while readable sources are still processed

### Evidence Organization & Integrity
- [ ] Evidence stored under `docs/evidence/<topic>/` with local conversion intermediates in a safe temporary location
- [ ] Source documents never modified
- [ ] No silent overwrites; user prompted before updating existing evidence sets
- [ ] Intermediates not staged or committed
- [ ] Partial results preserved when some inputs cannot be read

### Summarize Workflow
- [ ] `/summarize <evidence-path> <meeting|executive|technical|general> [topic]` produces Markdown summaries
- [ ] Meeting summaries include participants, topics, decisions, action items, owners, deadlines, unresolved questions (omit/label unsupported fields)
- [ ] Executive summaries include situation, business impact, recommendation, effort/timeline ranges, material risks, decisions required
- [ ] Technical summaries include current state, requirements, architecture, constraints, decisions, dependencies, risks
- [ ] General summaries are source-faithful with evidence citations
- [ ] Output written to `docs/deliverables/summaries/`
- [ ] User prompted before overwriting

### Estimate Workflow
- [ ] `/estimate <evidence-path> [scope]` produces Markdown estimates
- [ ] Includes scope, exclusions, assumptions, unresolved questions, work breakdown
- [ ] Provides optimistic, likely, pessimistic effort ranges with estimation unit and team assumptions
- [ ] Includes confidence levels, dependencies, risks, contingency rationale, timeline implications
- [ ] Cites source evidence for scope and constraints
- [ ] Distinguishes evidence-based values from estimator assumptions
- [ ] Avoids false precision; explains what new information could materially change estimate
- [ ] Output written to `docs/deliverables/estimates/`
- [ ] User prompted before overwriting

### Compare Workflow
- [ ] `/compare <evidence-path> <subject>` produces Markdown comparisons
- [ ] Identifies options, drivers, mandatory constraints, tradeoffs, costs, operational consequences, risks, reversibility, evidence gaps
- [ ] Uses decision matrix when criteria and scoring appropriate, with every score and weight explained
- [ ] Includes sensitivity analysis when close scores or uncertain weights could change result
- [ ] Provides recommendation only when evidence supports one; labels unsupported judgments as assumptions
- [ ] Remains exploratory and non-authoritative; directs to `/adr` for approved decisions
- [ ] Output written to `docs/deliverables/comparisons/`
- [ ] User prompted before overwriting

### Document Processing & Security
- [ ] No cloud document conversion, OCR, or artifact storage; inference uses the configured IBM ICA endpoint
- [ ] Document workers deny arbitrary webfetch/websearch, and confidential use requires an approved inference endpoint
- [ ] Source content treated as untrusted data with prompt-injection resistance
- [ ] Conversion commands narrowly scoped; source directories read-only
- [ ] Document-processing subagents have narrowly scoped write permissions to required output directories
- [ ] Unrelated source material not exposed or copied into deliverables
- [ ] Confidential document contents not logged unnecessarily

### Toolchain & Dependencies
- [ ] Missing local dependencies produce actionable diagnostics, no fabricated results
- [ ] Do not silently install large system dependencies
- [ ] DOCX, XLSX, PPTX extraction via checked-in scripts in `tools/` (narrowly scoped, version-controlled)
- [ ] Prefer smallest reliable local toolchain; LibreOffice headless acceptable for rendering
- [ ] Available LibreOffice is invoked headlessly with an isolated profile and timeout; failures produce PARTIAL coverage
- [ ] Office sources with external relationships skip LibreOffice rendering, preserve structured extraction, and become PARTIAL
- [ ] Declared PPTX slide relationships are authoritative; orphan slide members are ignored when `presentation.xml` exists
- [ ] Declared PPTX slides preserve original ordinals, and only media/charts/notes reachable from resolved declared slides are evidence
- [ ] XLSX absoluteAnchor visuals retain worksheet ownership and safe position/extent without fabricated cell ranges; unresolved anchors produce PARTIAL coverage
- [ ] Direct text/Markdown inputs are bounded at 10 MiB and direct PDF/image inputs at 100 MiB before payload read/copy
- [ ] Temporary conversion state remains within evidence directory or temporary location, never overwrites sources

### Workflow Integration & Reuse
- [ ] `/analyze` and `/adr` behavior remains usable
- [ ] `/ingest` and `/analyze` relationship clearly defined; prefer `/ingest` for normalization and reusable evidence, with `/analyze` consuming evidence or delegating to shared ingestion
- [ ] `/compare` separate from authoritative `/adr` decisions; existing Accepted ADRs are binding constraints when explicitly included

### Documentation & Testing
- [ ] README documents dependencies, supported formats, limitations, output locations, installation/restart steps
- [ ] Tests or fixtures cover: mixed-format ingestion, embedded visuals, multi-sheet XLSX, PPTX with notes and images, one unreadable input
- [ ] No source documents, generated evidence, deliverables, conversion outputs, or confidential fixture content staged/committed
- [ ] Existing workflows and configuration remain valid after installation

## Edge Cases & Error Handling

- **Unsupported legacy formats (DOC, XLS, PPT)**: Listed as input issues; processing continues for supported formats in the same batch
- **Embedded visuals in DOCX/XLSX/PPTX**: Extracted and preserved; if extraction fails, coverage marked PARTIAL and extraction method recorded
- **Wide XLSX sheets or hidden data**: Structured extraction records dimensions, visibility, hidden rows/columns, filters, types, dates, formulas, and limitations; rendering supplements but never replaces it
- **Lossy conversion (e.g., complex PPTX animations, VBA macros)**: Extraction method and coverage limitations explicitly recorded
- **External Office relationships**: Skip rendering without logging targets; preserve structured evidence and mark PARTIAL
- **Orphan PPTX slides**: Ignore package slide members not declared by an existing `presentation.xml`
- **Missing PPTX predecessor**: Preserve later declared slide ordinals in headings, notes, warnings, visuals, and citations
- **XLSX absoluteAnchor**: Record absolute position/extent when safe; otherwise warn and mark PARTIAL without inventing a cell range
- **Oversized direct input**: Fail only that source with an actionable size-limit issue and continue the batch
- **PDF with scanned images and embedded text**: Both textual (via OCR or PDF text layer) and visual evidence extracted when available
- **Existing evidence sets**: User prompted to confirm overwrite; no silent replacement
- **Conversion dependency missing**: Actionable diagnostic message provided; no fallback fabrication
- **Prompt injection in extracted text**: Extracted content treated as untrusted evidence; instructions within documents ignored
- **Temporary files and intermediates**: Cleaned up or stored safely under evidence directory; never left behind to overwrite sources
- **Partial results**: If some inputs fail, readable sources still processed and result marked PARTIAL with coverage details

## Dependencies & Constraints

### Technical Constraints
- **Local document processing**: No cloud conversion, OCR, or artifact-storage service; configured IBM ICA inference is not local
- **Supported input formats**: Plain text, Markdown, PDF, DOCX, XLSX, PPTX, standalone images (PNG, JPG, GIF, WebP, SVG)
- **Unsupported formats**: DOC, XLS, PPT (legacy Office); reported as explicit input issues
- **Output format**: Markdown only
- **Model capability**: gpt-5.6-sol supports text, image, and PDF inputs; configuration currently incorrect and must be updated
- **Lightweight model routing**: `gpt-5.6-luna` replaces Haiku 4.5 for `small_model`, explore/general/title/summary, spec-definer, spec-implementer-lite, and review-spec
- **Source integrity**: Never modify original documents
- **Evidence integrity**: Extract faithfully; do not fabricate visual, textual, spreadsheet, or presentation content

### Workflow Dependencies
- Extends existing `/analyze` workflow; reuses or clearly defines relationship
- Reuses `/adr` for authoritative decisions; `/compare` remains advisory
- Uses existing S1, S2 source ID pattern from doc-analyze
- Respects existing permission boundaries and output directory conventions
- Maintains compatibility with spec-plan (no automatic integration required)

### Local Toolchain
- Document conversion via checked-in scripts in `tools/` (narrowly scoped)
- Likely dependencies: pandoc or LibreOffice headless for DOCX → text+images; openpyxl or similar for XLSX parsing; python-pptx for PPTX extraction; standard PDF and image libraries
- Installation diagnostics required; no silent dependency installation
- Temporary state managed within evidence directory or dedicated temporary location

### Scope & Governance
- No automatic Office-format output (Markdown only)
- No automatic spec-plan integration beyond reuse of existing evidence
- No speculative permissions or generic frameworks
- Keep implementation minimal; YAGNI principles apply
- Do not create separate agent unless concrete permission boundary or responsibility difference justifies it

## Out of Scope

- DOC, XLS, and PPT legacy Office formats
- Cloud-based conversion, OCR, or document-processing services
- Automatically generated DOCX, XLSX, or PPTX deliverables
- Automatic web research or arbitrary external API calls beyond the configured IBM ICA inference endpoint
- Automatically updating estimates when evidence changes
- Automatically accepting architecture decisions
- A generic plugin or MCP server unless planning demonstrates necessity
- Fixing the unrelated `session_message.seq` database error
- Automatic integration into spec-plan workflow

## Notes

### Unresolved Implementation Choices (to be finalized in planning)

- **Local conversion approach**: Confirmed as checked-in scripts in `tools/` (narrowly scoped, version-controlled)
- **Exact evidence directory structure**: Details to be defined during planning (e.g., `docs/evidence/<topic>/sources.json`, normalized outputs, intermediates location)
- **Subagent assignment**: Assess during planning whether existing doc-analyst or a new document-writing subagent provides the cleanest permission boundary
- **Test fixture strategy**: How to cover required scenarios (mixed formats, embedded visuals, multi-sheet XLSX, PPTX with notes/images, unreadable input) without committing confidential client material

### Context & Rationale

- **Privacy boundary**: Conversion and storage remain local; confidential use requires approval of the configured IBM ICA inference endpoint
- **Why checked-in scripts?** Version-controlled conversion tools ensure reproducibility and auditability
- **Why reuse `/analyze` and `/adr`?** Avoid duplicate analysis logic; leverage existing workflows where they fit
- **Why distinguish direct evidence from inference?** Deliverables must be traceable; conflating facts with assumptions undermines client trust
- **Why PARTIAL coverage instead of failing?** Real-world document batches often include mixed-quality or legacy sources; preserve usable results
- **Why treat extracted content as untrusted?** Documents may contain embedded instructions or adversarial content; strict evidence boundaries protect agent behavior
- **Why multiple summary templates?** Different stakeholders (executives, engineers, project managers) need different structure and depth
- **Why evidence-based ranges over point estimates?** Confidence and contingency must be visible; false precision damages credibility

### References

- Existing workflows: `/analyze`, `/adr`, doc-analyst, doc-analyze skill
- Global governance: AGENTS.md (YAGNI, no speculative abstraction, no single-use wrappers, epistemological honesty)
- Model capability: gpt-5.6-sol (text, image, PDF support; configuration to be corrected)
- Permission patterns: Existing subagent output directory restrictions and narrowly scoped command permissions
