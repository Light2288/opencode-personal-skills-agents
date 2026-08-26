# Opencode Tier 1: Hardening Config & Workflows

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Opencode Tier 1: Hardening Config & Workflows          |
| **Type**      | chore                                                  |
| **Scope**     | ~/.config/opencode/ (agents, skills, config)           |
| **Created**   | 2026-08-25 20:00:00                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

The opencode config (in ~/.config/opencode and mirrored to opencode-personal-skills-agents repo) has internal contradictions, missing governance, and inefficient workflows that need to be fixed before Tier 2 (review/debug agents) and Tier 3 (architecture agents) work can proceed cleanly.

Current pain points:

1. **Write-approval contradiction**: Skills (spec-define/SKILL.md, spec-plan/SKILL.md) contradict agent hard rules (spec-definer.md, spec-planner.md) on whether drafts are written before or after user approval. Line 131 vs line 203 in spec-define/SKILL.md; line 163 vs line 237 in spec-plan/SKILL.md.

2. **Missing output governance**: No global rules defining how all agents should write (YAGNI, no speculative abstraction, concise, comments for why, etc.). Without this, future Tier 2/3 agents will inherit inconsistent output styles.

3. **Inefficient codebase exploration**: spec-plan and spec-implement both spend Opus tokens reading files and globbing when a lightweight Haiku explorer agent could do this work once, in parallel.

4. **Incomplete config**: opencode.json lacks step budgets for spec-implementer; baseURL contains secrets (IBM endpoint); agent routing to Haiku is partial (spec-definer has it, but spec-planner and spec-implementer use defaults).

5. **No command entry points**: No `/define`, `/plan`, `/implement` shortcuts to invoke the right agent; users must manually invoke the task tool.

## Desired Outcome

After Tier 1 is complete:

- **Single, coherent narrative** for write-then-review workflows across all skills and agent hard rules. Status lifecycle: DRAFT → review → DEFINED (for spec-define), DEFINED → review → PLANNED (for spec-plan).
- **Global AGENTS.md** in ~/.config/opencode/ that sets output-shaping rules and epistemological honesty rules. Registered in opencode.json's `instructions` key. Applied to all agents, all sessions.
- **Explore agent delegation** in spec-plan Step 2 and spec-implement Step 2: instead of doing glob/grep/read in-context on Opus, ask explore agent (Haiku) to digest the codebase and return a compact summary.
- **Locked-down, templatable config**: opencode.json sanitized (baseURL placeholder), spec-implementer has explicit step budget (150), Haiku routing for title/summary/scout agents, compaction verified safe.
- **Command shortcuts** at ~/.config/opencode/command/*.md (/define, /plan, /implement) routing to the right agent via frontmatter.

All changes remain usable in ~/.config/opencode after copy; no secrets committed.

## Acceptance Criteria

- [ ] Reconcile write-before-approval contradiction: Remove 3 contradictory lines from spec-define/SKILL.md and spec-plan/SKILL.md; update spec-definer.md and spec-planner.md hard rule #3 to match single narrative ("write DRAFT, ask review, flip DEFINED").
- [ ] Create ~/.config/opencode/AGENTS.md (~60 lines): YAGNI, no speculative abstraction, no single-use wrappers, comments only for why, no silent catch, no dead code, project conventions, concise, epistemological honesty. Register via `"instructions": ["AGENTS.md"]` in opencode.json.
- [ ] Update spec-plan/SKILL.md Step 2: delegate codebase exploration to explore agent; spec-plan receives compact digest instead of doing glob/grep/read in-context.
- [ ] Update spec-implement/SKILL.md Step 2: same delegation to explore agent; receive compact digest.
- [ ] Update opencode.json: add `"steps": 150` to spec-implementer; sanitize baseURL to `<YOUR_PROVIDER_BASE_URL>`; route title/summary/scout agents to Haiku (if agent definitions exist); verify compaction.prune does not prune skill tool output.
- [ ] Create ~/.config/opencode/command/define.md, /plan.md, /implement.md: each routes to the right agent (spec-definer, spec-planner, spec-implementer) via frontmatter `agent:` key.
- [ ] All changed files remain usable in ~/.config/opencode after copy from the opencode-personal-skills-agents repo.

## Edge Cases & Error Handling

- **Multiple spec-implementer-lite references**: spec-implementer-lite.md exists but has no steps config. If Tier 1 adds steps to spec-implementer, verify spec-implementer-lite remains at lower step count (120 as noted in context) to preserve tier ordering.
- **Explore agent availability**: If explore agent is not loaded or unavailable during plan/implement, gracefully fall back to in-context glob/grep (document the fallback in the skill).
- **Secret leakage in baseURL**: After sanitizing to placeholder, document in the spec that implementers must replace `<YOUR_PROVIDER_BASE_URL>` with their actual IBM ICA or other provider endpoint before deployment.
- **Command file registration**: If ~/.config/opencode/command/ does not exist, create it. Ensure opencode.json or a startup script discovers and registers .md files in that directory (may require opencode core support).

## Dependencies & Constraints

- **Git repo constraint**: The source repo (opencode-personal-skills-agents) is a git repo, but files will be copied to ~/.config/opencode/ for daily use. No secrets (API keys, baseURL endpoints) may be hardcoded; placeholders required.
- **Opencode core behavior**: Verify that compaction.prune does not prune `skill` tool output (spec defines this is safe; confirm during implementation).
- **Agent model assignments**: spec-implementer currently hardcodes `model: ibm-ica/claude-opus-5` in frontmatter. Haiku routing should not override this; title/summary/scout agents may use Haiku. Clarify in plan if Tier 1 should touch model assignments.
- **Step budget semantics**: `steps` controls reasoning-loop depth in opencode. 150 for spec-implementer is a ceiling, not a typical usage. Document meaning in the plan.

## Out of Scope

- **Tier 2 (review/debug agents)**: Any agent for code review, test debugging, or runtime issue diagnosis. Separate spec.
- **Tier 3 (architecture agents)**: Any agent for codebase refactoring, architecture analysis, or cross-cutting concerns. Separate spec.
- **Opencode core changes**: This spec does not modify opencode's runtime, command-line parsing, or MCP server behavior. Configuration only.
- **Agent functionality changes**: Tier 1 does not alter what spec-definer, spec-planner, or spec-implementer do — only how they are wired and governed.
- **Documentation site updates**: README, blog, or website changes are out of scope; this is config-only.

## Notes

- **Slug confirmation**: The slug is `opencode-tier1-fixes` (already provided).
- **Directory structure**: After Tier 1, the repo should have:
  - `specs/opencode-tier1-fixes.md` (this spec)
  - `plans/opencode-tier1-fixes.md` (to be produced by spec-plan)
  - `~/.config/opencode/AGENTS.md` (new)
  - `~/.config/opencode/command/define.md`, `/plan.md`, `/implement.md` (new)
  - Modified: `~/.config/opencode/opencode.json`, agent hard rules, skill workflows
- **Implementation sequencing**: Changes to opencode.json and skills should be coordinated to avoid breaking the workflow mid-implementation. Recommend: fix agent hard rules first, then skills, then config, then AGENTS.md, then commands.
- **Testing the fixes**: After implementation, spot-check: run /define on a toy spec, verify draft is written immediately; verify hard rule #3 text is gone; verify AGENTS.md is injected into all agent contexts; verify explore delegation works in spec-plan.

## Post-Implementation Amendments

- **Provider baseURL**: The repository config carries a
  `provider.ibm-ica.options.baseURL` that references an external, untracked
  file via opencode's `{file:...}` substitution
  (`{file:~/.config/opencode/ibm-ica-baseurl}`). The real endpoint is never
  committed — it lives only in that local file, which the user creates
  outside version control. `install.sh` copies `opencode.json` verbatim and
  prints a non-fatal warning if the file is missing on a fresh machine.
  (`{env:...}` is not used: it is unreliable for the GUI-launched desktop app
  and resolves to an empty string when unset.)
- **Haiku routing**: The delivered `opencode.json` explicitly routes the valid built-in `title` and `summary` agents to `ibm-ica/claude-haiku-4-5`, alongside `explore` and `general`. `scout` routing is inapplicable because OpenCode 1.15.4 registers scout only behind an experimental runtime flag and this installation does not expose a scout agent.
