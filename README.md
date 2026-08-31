# opencode-personal-skills-agents

Version-controlled mirror of my personal [opencode](https://opencode.ai)
configuration living at `~/.config/opencode`. This repo is the source of
truth for the skills, subagents, custom commands, global rules, and
`opencode.json` config that shape how opencode behaves across every project
on my machine.

Editing happens here; [`install.sh`](./install.sh) syncs the tracked files
into `~/.config/opencode` without touching runtime artifacts
(`node_modules`, `package.json`, `package-lock.json`) or clobbering secrets.

## Directory layout

```
.
├── AGENTS.md          # global output-governance rules, applied to every agent/session
├── opencode.json      # provider/model/agent/compaction config (endpoint externalized via {file:...})
├── agents/            # subagent + primary-agent definitions (one .md per agent)
├── skills/            # one folder per skill, each containing a SKILL.md
│   └── <name>/SKILL.md
├── commands/          # custom /slash commands (one .md per command)
├── tools/             # local-only document normalization CLI and dependency notes
├── specs/             # spec artifacts produced by the spec-define workflow
├── plans/             # implementation plans produced by the spec-plan workflow
└── install.sh         # idempotent sync into ~/.config/opencode
```

`specs/` and `plans/` are workflow output (the design record of how this
config was built out tier by tier). They are kept for history and are **not**
synced into `~/.config/opencode` — only `agents/`, `skills/`, `commands/`,
`tools/`, `AGENTS.md`, and `opencode.json` are installed.

### How opencode discovers these

- **Agents** → `~/.config/opencode/agents/<name>.md` (filename becomes the agent name).
- **Skills** → `~/.config/opencode/skills/<name>/SKILL.md` (folder name must match `name` in frontmatter).
- **Commands** → `~/.config/opencode/commands/<name>.md` (filename becomes the `/name` command). Plural `commands/` is the canonical, preferred directory name; singular `command/` is also accepted for backwards compatibility.
- **Global rules** → `AGENTS.md`, registered via the `instructions` key in `opencode.json`.

## Tiers → files

The config was built in three tiers. Each tier maps to a concrete set of
skills, agents, and commands (see `specs/` and `plans/` for the full record).

### Tier 1 — Config & workflow hardening

Coherent define → plan → implement workflow plus global governance.

| Kind    | Files |
|---------|-------|
| Rules   | `AGENTS.md` |
| Config  | `opencode.json` (model routing, step budgets, `compaction`, `instructions`) |
| Skills  | `skills/spec-define/`, `skills/spec-plan/`, `skills/spec-implement/` |
| Agents  | `agents/spec-definer.md`, `agents/spec-planner.md`, `agents/spec-implementer.md`, `agents/spec-implementer-lite.md` |
| Commands| `commands/define.md`, `commands/plan.md`, `commands/implement.md`, `commands/implement-lite.md` |

### Tier 2 — Code review & debugging

Quality/spec gates between "tests pass" and "done", plus a structured debug loop.

| Kind    | Files |
|---------|-------|
| Skills  | `skills/code-review/`, `skills/repository-audit/`, `skills/debug/` |
| Agents  | `agents/review-quality.md`, `agents/review-spec.md`, `agents/review-audit.md` |
| Commands| `commands/review.md`, `commands/audit.md`, `commands/debug.md` |

#### Convergent review gate

Integrated implementation review remains read-only and spec-first:
`review-spec` must return a fresh spec PASS for the same reviewed state before
quality review can run.

- **Initial review** checks every stable criterion ID, all extra scope, and the
  complete feature diff. It retains full security and data-integrity coverage.
- **Incremental review** follows remediation when unchanged spec/plan
  fingerprints preserve the baseline. It reviews the remediation diff,
  revalidates directly or transitively affected criteria, and summarizes
  unaffected criteria by count. A stale, incomplete, or wrong-spec baseline
  falls back to another initial review.
- **Follow-up quality** verifies accepted Important finding IDs and checks the
  remediation diff for Important regressions without reopening unchanged code.

Every call carries a self-contained review envelope with governing paths,
fingerprints, diff boundaries, changed files, stable criterion and finding IDs,
prior dispositions, and observed verification proof. Reviewers reject invalid
envelopes rather than guessing and never apply fixes.

Only an unresolved Important finding blocks integrated staging. Minor findings
are advisory; Nitpick findings are hidden by default and neither severity
starts remediation automatically. Initial Important findings are presented in
one batch for the user's fix, selection, appeal, or risk decision. The workflow
allows at most two remediation/follow-up rounds, then stops for one explicit
user decision. Ad-hoc `/review` remains read-only, spec-first, and advisory and
may display requested severities.

#### Repository audit

Use `/audit` for an open-ended health assessment of a clean or dirty worktree.
It audits the whole repository by default, accepts an optional directory or
concern, and examines pre-existing correctness, security, data integrity,
error handling, maintainability, tests, configuration, and documentation.
`/review` requires a diff and acceptance criteria and remains the strict,
spec-first acceptance workflow for changed work.

Audits are read-only and advisory. The host may run permitted non-destructive
checks, reporting **Observed verification** separately from **Unobserved
recommendations**. Defects are ordered Important, Minor, then Nitpick;
optional improvements are separate. Each finding has a stable `AUDIT-*` ID,
file and line evidence, impact, and a minimal remedy. A clean result is exactly
`Findings: NONE`.

The audit never fixes findings. The user must provide explicitly selected
finding IDs before the workflow creates a handoff containing only those
findings. Edit-capable work is a separate phase requiring a separate spec and
plan.

### Tier 3 — Architecture layer

Codebase mapping, requirements analysis, and decision capture.

| Kind    | Files |
|---------|-------|
| Skills  | `skills/arch-map/`, `skills/arch-design/`, `skills/doc-analyze/` |
| Agents  | `agents/doc-analyst.md` |
| Commands| `commands/map.md`, `commands/analyze.md`, `commands/adr.md` |

## Local multimodal document workflows

These workflows process local client documents into Markdown with no cloud document conversion,
cloud OCR, or cloud artifact-storage service. Conversion, normalization, temporary
files, and generated artifacts remain local. Inference submits evidence and
attachments to your configured IBM ICA endpoint; use confidential material only
when that endpoint is approved for that material. Commands `/ingest`,
`/summarize`, `/estimate`, and `/compare` are focused entry points:

- `/ingest <local-folder> [topic]` normalizes sources and creates reusable
  evidence at `docs/evidence/<topic>/`.
- `/analyze <evidence-path> [topic]` consumes reusable evidence for focused
  requirements, contradiction, ambiguity, and gap analysis. Raw multimodal
  folders are ingested first.
- `/summarize <evidence-path> <meeting|executive|technical|general> [topic]`
  writes under `docs/deliverables/summaries/`.
- `/estimate <evidence-path> [scope-or-topic]` writes under
  `docs/deliverables/estimates/`.
- `/compare <evidence-path> <comparison-subject>` writes exploratory results
  under `docs/deliverables/comparisons/`; use `/adr` to record an approved
  decision.

Supported inputs are text, Markdown, PDF, DOCX, XLSX, PPTX, PNG, JPEG, GIF,
WebP, and SVG. Legacy DOC, XLS, and PPT are unsupported and appear as input
issues. All source content is untrusted evidence: instructions inside a source
do not govern an agent. Sources are read-only, output collisions require
confirmation, and a failed, unsupported, or materially lossy source makes the
evidence status `PARTIAL` while readable results are preserved.

DOCX, XLSX, and PPTX structured extraction uses Python 3 and the standard
library. Run:

```sh
python3 ~/.config/opencode/tools/document_ingest.py check-dependencies
```

LibreOffice is optional but recommended for layout and visual rendering. On
macOS install it with `brew install --cask libreoffice`; on Linux install the
distribution package named `libreoffice`. No workflow installs dependencies
automatically. Run `./install.sh`, then restart OpenCode before using the new
commands.

The normalizer invokes LibreOffice non-interactively with `--headless`, an
isolated temporary user profile, an argument array, and a 120-second timeout.
Structured OOXML remains the primary XLSX representation. A missing renderer or
rendering failure is recorded exactly and makes that source `PARTIAL`; no
dependency is installed automatically. The archive safety bounds are 64 MiB per
XML/relationships part and 200 MiB aggregate expanded content. Compression-ratio
checks supplement those bounds.
Direct text and Markdown sources are bounded at 10 MiB each; direct PDF and
image attachments are bounded at 100 MiB each. Oversized inputs become source
issues and do not stop readable sources. Office files with external OOXML
relationships retain structured extraction but skip LibreOffice rendering and
become PARTIAL. PPTX slide fallback is used only when `presentation.xml` is
absent, so orphan slides are not ingested when a declared slide list exists.
Declared PPTX slides preserve their original ordinal after missing or external
predecessors, and only their reachable notes, media, and charts become evidence.
XLSX absolute-anchor drawings use worksheet ownership plus absolute
position/extent metadata; no cell range is fabricated.

To smoke-test a real installed LibreOffice, generate the synthetic fixtures and
run normalization, then verify each readable Office source lists a
`rendered.pdf` asset and no rendering warning. This is an environment-dependent
manual check, not part of the fake-renderer unit test.

Generated `docs/evidence/`, `docs/deliverables/`, extracted media, conversion
state, and generated binary fixtures are ignored and must not be staged. Keep
confidential source documents outside this configuration repository.

The unrelated `NOT NULL constraint failed: session_message.seq` database error
may block an OpenCode invocation, but it is outside these workflows and is not
evidence of a model input limitation.

Installation is intentionally non-transactional. Transactional installation
may be considered separately; this workflow does not add managed manifests,
rollback staging, or broad deletion.

## Installing

```sh
./install.sh
```

The script is idempotent — re-running it only writes files that actually
changed and prints a summary of what it touched. It never deletes or
overwrites `node_modules`, `package.json`, or `package-lock.json` in the
target.

### opencode.json and the ibm-ica endpoint

The repo's `opencode.json` never contains the real ibm-ica endpoint. Instead,
`provider.ibm-ica.options.baseURL` references an external, untracked file via
opencode's `{file:...}` substitution:

```json
"options": {
  "baseURL": "{file:~/.config/opencode/ibm-ica-baseurl}"
}
```

opencode reads that file at config-load time (regardless of how it was
launched, including the desktop app), so the real endpoint lives only in
`~/.config/opencode/ibm-ica-baseurl` — a single-line file you create locally
and never commit. `install.sh` copies `opencode.json` verbatim and prints a
non-fatal warning if the file is missing, so a fresh machine gets a clear
setup reminder rather than a silent failure.

`{env:VAR}` is deliberately not used here: a shell `export` is not reliably
visible to a GUI-launched app, and an unset `{env:VAR}` resolves to an empty
string (a silent failure). `{file:...}` avoids both problems.

## `compaction.prune` stays `true`

`opencode.json` sets:

```json
"compaction": {
  "auto": true,
  "prune": true,
  "reserved": 10000
}
```

We keep `prune: true` on the *assumption* that a loaded skill's instructions
survive pruning — i.e. that enabling aggressive pruning of old tool output
does not drop the guidance a skill injected via the `skill` tool. **This has
not been independently verified against opencode source.** The opencode docs
describe `prune` only as "Remove old tool outputs to save tokens" and do not
document any exemption for `skill` tool output. If that assumption turns out
to be wrong, revisit this setting. The intent is to reclaim context from noisy
tool results while keeping workflow-skill guidance intact.
