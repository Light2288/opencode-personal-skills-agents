# Plan: Opencode Tier 1: Hardening Config & Workflows

| Field        | Value                                     |
|--------------|-------------------------------------------|
| **Title**    | Opencode Tier 1: Hardening Config & Workflows |
| **Spec**     | specs/opencode-tier1-fixes.md              |
| **Type**     | chore                                     |
| **Branch**   | chore/opencode-tier1-fixes                |
| **Created**  | 2026-08-25 20:30:00                       |
| **Status**   | IMPLEMENTED                               |

## Context

The opencode personal-skills-agents config has internal contradictions between agent hard rules and skill workflows (write-before-approval timing), missing global governance (AGENTS.md), inefficient codebase exploration (Opus vs. delegated Haiku), incomplete config (baseURL with secrets, missing step budgets, missing instructions), and no command shortcuts (/define, /plan, /implement). This plan reconciles contradictions, establishes governance, delegates exploration, sanitizes config, and creates command entry points.

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. The branch
> name is `chore/opencode-tier1-fixes` (see mapping below).
>
> Reference command (the implementer adapts to the detected base):
>
> ```bash
> git checkout <base> && git pull --ff-only && git checkout -b chore/opencode-tier1-fixes
> ```
>
> If the repo is not a git workspace, branch creation is skipped and
> noted in the implementation report.

Branch type mapping:

- feature → `feat/<slug>`
- bug → `fix/<slug>`
- refactor → `refactor/<slug>`
- chore → `chore/<slug>`

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Each task in the Tasks section maps to exactly one commit.

## Build & Test Commands

| Action | Command |
|--------|---------|
| Validate config | `opencode run "list skills"` (verify agents/skills load without errors) |
| Verify instructions | Check that AGENTS.md is injected into all agent contexts |

(This is a config/markdown project with no test framework. Verification focuses on schema validation, load success, and workflow coherence; see Verification section.)

## Tasks

### Task 1: Reconcile write-approval contradiction in spec-definer hard rule `[S]`

**Goal**: Remove the write-before-approval prohibition from spec-definer's hard rule #3 and replace it with a clear statement that drafts ARE written immediately, but approval gates the status flip to DEFINED.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/agents/spec-definer.md` | modify | Update hard rule #3 (lines 42–44) to clarify: draft written immediately; approval gates status flip in Step 5 |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `~/.config/opencode/skills/spec-define/SKILL.md` | Existing narrative: write DRAFT in Step 4, ask review, flip DEFINED in Step 5 |

**Steps**:

1. Open spec-definer.md and locate hard rule #3 (lines 42–44).
2. Replace the prohibition "You never write the spec file before the user explicitly approves the draft" with a clarification: "You write the draft immediately (DRAFT status); approval gates the flip to DEFINED (Step 5). Drafting in chat is fine before writing to disk. Calling write is fine for DRAFT; flipping status requires approval."
3. Align this phrasing with the skill's Step 4–5 narrative to ensure single thread.

**Tests**:

- Read the updated hard rule #3 and confirm it no longer contradicts spec-define/SKILL.md Step 4–5.
- Verify the rule is ~2 sentences, concise and clear.

**Acceptance criteria covered**: Criterion 1 (reconcile write-approval contradiction).

**Commit**: `chore(spec-definer): clarify hard rule #3 on write-before-approval workflow`

---

### Task 2: Reconcile write-approval contradiction in spec-planner hard rule `[S]`

**Goal**: Remove the write-before-approval prohibition from spec-planner's hard rule #3 and replace it with a clear statement matching spec-definer's and spec-plan/SKILL.md workflow.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/agents/spec-planner.md` | modify | Update hard rule #3 (lines 50–52) to clarify: draft written immediately; approval gates status flip in Step 4 |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `~/.config/opencode/skills/spec-plan/SKILL.md` | Existing narrative: write DRAFT in Step 3, ask review, flip PLANNED in Step 4 |

**Steps**:

1. Open spec-planner.md and locate hard rule #3 (lines 50–52).
2. Replace the prohibition with the same clarification as spec-definer, adapted for spec-plan: "You write the draft immediately (DRAFT status); approval gates the flip to PLANNED (Step 4). Drafting in chat is fine before writing to disk. Calling write is fine for DRAFT; flipping status requires approval."
3. Ensure alignment with spec-plan/SKILL.md Step 3–4 narrative.

**Tests**:

- Read the updated hard rule #3 and confirm it no longer contradicts spec-plan/SKILL.md Step 3–4.
- Verify the rule is ~2 sentences, concise and clear.

**Acceptance criteria covered**: Criterion 1 (reconcile write-approval contradiction).

**Commit**: `chore(spec-planner): clarify hard rule #3 on write-before-approval workflow`

---

### Task 3: Remove contradictory guideline from spec-define/SKILL.md `[S]`

**Goal**: Remove or reword the contradictory guideline at line 203 that says "Never write the file before the user approves the draft", which contradicts the actual Step 4–5 workflow that writes DRAFT immediately.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/skills/spec-define/SKILL.md` | modify | Remove/reword line 203 guideline in Guidelines section |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Task 1 (spec-definer hard rule #3) | Narrative already established |

**Steps**:

1. Open spec-define/SKILL.md and locate line 203 in the Guidelines section.
2. Either remove the line entirely (if it's now redundant after Task 1) or reword it to "Never flip to DEFINED before the user approves the draft" to match the actual workflow.
3. Verify the Guidelines section now accurately reflects the write-DRAFT-first workflow.

**Tests**:

- Read the Guidelines section and confirm no contradiction remains between line 131 (write first), line 137–144 (write with DRAFT status), and line 203 (now clarified or removed).

**Acceptance criteria covered**: Criterion 1 (reconcile write-approval contradiction).

**Commit**: `chore(spec-define): remove contradictory guideline on write timing`

---

### Task 4: Remove contradictory guideline from spec-plan/SKILL.md `[S]`

**Goal**: Remove or reword the contradictory guideline at line 237 that says "Never write the plan before the user approves the draft", which contradicts the actual Step 3–4 workflow that writes DRAFT immediately.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/skills/spec-plan/SKILL.md` | modify | Remove/reword line 237 guideline in Guidelines section |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Task 2 (spec-planner hard rule #3) | Narrative already established |

**Steps**:

1. Open spec-plan/SKILL.md and locate line 237 in the Guidelines section.
2. Either remove the line entirely or reword it to "Never flip to PLANNED before the user approves the draft" to match the actual workflow.
3. Verify the Guidelines section now accurately reflects the write-DRAFT-first workflow.

**Tests**:

- Read the Guidelines section and confirm no contradiction remains between line 163 (write first), line 171–174 (write with DRAFT status), and line 237 (now clarified or removed).

**Acceptance criteria covered**: Criterion 1 (reconcile write-approval contradiction).

**Commit**: `chore(spec-plan): remove contradictory guideline on write timing`

---

### Task 5: Create AGENTS.md with global output governance `[M]`

**Goal**: Create a new file `~/.config/opencode/AGENTS.md` (~60 lines) that establishes global output-shaping rules and epistemological honesty rules for all agents. This file will be registered in opencode.json's `instructions` key so it is injected into every agent context.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/AGENTS.md` | create | New file with ~60 lines of global governance rules |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Existing agent definitions (spec-definer.md, spec-planner.md, spec-implementer.md) | Patterns and conventions already in use |

**Steps**:

1. Create `~/.config/opencode/AGENTS.md` with the following sections:
   - **Preamble** (2–3 lines): brief description that this file establishes output standards for all agents.
   - **YAGNI** (3–4 lines): You Aren't Gonna Need It — don't invent abstractions, generics, or utilities until a second use case appears; solve the immediate problem.
   - **No speculative abstraction** (2–3 lines): don't wrap functions, classes, or patterns in utility layers without a clear, immediate need.
   - **No single-use wrappers** (2–3 lines): a wrapper exists only if it encapsulates complexity that occurs in 2+ places.
   - **Comments only for why** (2–3 lines): comments explain intent, design decisions, non-obvious tradeoffs; they do not repeat what the code says.
   - **No silent catch** (2–3 lines): all exception handling is explicit; no catch-alls or silent failures. If you catch, you handle, log, or re-throw with context.
   - **No dead code** (2–3 lines): remove unused imports, variables, functions, and branches. Dead code misleads future readers.
   - **Project conventions** (3–4 lines): follow the patterns established in the project (e.g., naming, structure, tool usage). If unsure, ask or match existing code.
   - **Concise output** (2–3 lines): be direct; avoid jargon, filler, and unnecessary explanation. One sentence per action; no throat-clearing.
   - **Epistemological honesty** (4–5 lines): admit uncertainty. Say "I don't know" or "I'm not sure" rather than guessing. Distinguish between facts (what you've read/verified in code) and inference (what you assume). Flag edge cases you haven't tested.

2. Save the file with ~60 lines total.
3. Ensure the file is in Markdown or plain text, readable and enforceable (agents should be able to understand it as a constraint).

**Tests**:

- Verify the file exists and is ~60 lines.
- Read it and confirm all 10 governance rules are covered.
- Verify it is plain-language, actionable, and not overly bureaucratic.

**Acceptance criteria covered**: Criterion 2 (create AGENTS.md with global output rules).

**Commit**: `chore(agents): create AGENTS.md with global output governance rules`

---

### Task 6: Register AGENTS.md in opencode.json instructions `[S]`

**Goal**: Add AGENTS.md to the `instructions` key in opencode.json so it is automatically injected into all agent contexts during initialization.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/opencode.json` | modify | Add or update `"instructions": ["AGENTS.md"]` at root level |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Task 5 (AGENTS.md) | New governance file |

**Steps**:

1. Open opencode.json and locate the root-level configuration (e.g., after the `compaction` section).
2. If an `instructions` key does not exist, add `"instructions": ["AGENTS.md"]`.
3. If `instructions` already exists (unlikely), append `"AGENTS.md"` to the list.
4. Verify the JSON is valid (no syntax errors).
5. Ensure the file path resolves to `~/.config/opencode/AGENTS.md` (opencode.json is in that directory, so a relative path "AGENTS.md" should work).

**Tests**:

- Validate opencode.json against its schema (e.g., `opencode run "list agents"` or similar validation command).
- Confirm the file is valid JSON.

**Acceptance criteria covered**: Criterion 2 (register AGENTS.md for injection).

**Commit**: `chore(config): register AGENTS.md in opencode.json instructions`

---

### Task 7: Update spec-plan/SKILL.md to delegate codebase exploration `[M]`

**Goal**: Modify spec-plan/SKILL.md Step 2 to delegate codebase exploration to the explore agent (Haiku) instead of doing in-context glob/grep/read on the Opus agent. This frees Opus tokens and allows parallel exploration.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/skills/spec-plan/SKILL.md` | modify | Update Step 2 (lines 31–45) to delegate exploration to explore agent |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Existing explore agent pattern (e.g., from spec-implement) | If explore agent is already used elsewhere, follow the same delegation pattern |

**Steps**:

1. Open spec-plan/SKILL.md and locate Step 2 — "Explore the Codebase" (lines 31–45).
2. Replace the current approach (in-context glob/grep/read/bash) with a task tool call that delegates to the explore agent:
   - Instead of the planner doing glob/grep/read directly, call the `task` tool with `subagent_type: explore` and request a compact digest of the codebase structure, existing patterns, testing conventions, and any files/functions relevant to the spec.
   - Ask explore agent to return a structured JSON summary (e.g., file inventory, patterns, testing framework, build commands, relevant code).
3. Update the step description to reflect the new workflow: "Delegate codebase exploration to the explore agent; receive a compact digest summarizing project structure, existing patterns, and testing conventions."
4. Add a note about graceful fallback (if explore agent is unavailable, fall back to in-context glob/grep, but document this in the implementation report).
5. Keep the subsections (project structure, code patterns, testing, manifest files) but reframe them as "items explore agent should return" rather than "steps the planner performs".

**Tests**:

- Verify the step now describes delegation, not in-context tools.
- Confirm the planner receives a compact digest that grounds subsequent planning (Tasks section) in real files.
- Check that no critical information is lost compared to the current in-context approach.

**Acceptance criteria covered**: Criterion 3 (delegate spec-plan exploration).

**Commit**: `chore(spec-plan): delegate codebase exploration to explore agent`

---

### Task 8: Update spec-implement/SKILL.md to delegate codebase exploration `[M]`

**Goal**: Modify spec-implement/SKILL.md Step 2 to delegate initial codebase exploration to the explore agent (Haiku), similar to Task 7. The implementer focuses on TDD and implementation; exploration uses a lighter agent.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/skills/spec-implement/SKILL.md` | modify | Update Step 2 to delegate exploration to explore agent; keep manifest/build-command inspection local |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Task 7 (spec-plan delegation pattern) | Same explore agent delegation approach |

**Steps**:

1. Open spec-implement/SKILL.md and locate Step 2 (currently around lines 41–54, "Confirm build & test commands").
2. Modify the step to delegate non-local codebase exploration to explore agent:
   - Implementer still inspects package.json/Makefile/etc. directly to extract build/test commands (these are local, quick reads).
   - Implementer calls task tool with explore agent for broader codebase understanding (existing code structure, testing patterns, conventions).
3. Reframe Step 2 as: "Extract build & test commands from manifest files locally (package.json, Makefile, etc.); delegate broader codebase exploration (structure, patterns, conventions) to explore agent."
4. Add fallback note (same as Task 7).

**Tests**:

- Verify the step describes delegation for broader exploration while keeping manifest inspection local.
- Confirm the implementer receives a compact digest and build/test commands together, enabling Task-by-task implementation to begin.

**Acceptance criteria covered**: Criterion 4 (delegate spec-implement exploration).

**Commit**: `chore(spec-implement): delegate codebase exploration to explore agent`

---

### Task 9: Sanitize baseURL in opencode.json `[S]`

**Goal**: Replace the exposed IBM endpoint in opencode.json's `baseURL` field with a placeholder `<YOUR_PROVIDER_BASE_URL>` so no secrets are committed to the repo or leaked in ~/.config/opencode/.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/opencode.json` | modify | Replace line 8 baseURL endpoint with placeholder |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Existing opencode.json structure | No changes to structure; only value replacement |

**Steps**:

1. Open opencode.json and locate the `baseURL` field (line 8): currently `"https://api.servicesessentials.ibm.com/v1"`.
2. Replace the value with `"<YOUR_PROVIDER_BASE_URL>"`.
3. Verify JSON is still valid.
4. Add a note in the plan's Verification section that implementers must replace this placeholder with their actual endpoint before deployment.

**Tests**:

- Validate opencode.json against schema.
- Confirm the placeholder is present and no endpoint is exposed.

**Acceptance criteria covered**: Criterion 5 (sanitize baseURL in opencode.json).

**Commit**: `chore(config): sanitize baseURL to placeholder in opencode.json`

---

### Task 10: Add step budget to spec-implementer in opencode.json `[S]`

**Goal**: Add `"steps": 150` to the spec-implementer agent definition in opencode.json to set an explicit reasoning-loop budget, enabling more complex TDD workflows without token exhaustion.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/opencode.json` | modify | Add `"steps": 150` to agent.spec-implementer definition |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Existing spec-implementer-lite definition | spec-implementer-lite has `"steps": 120`; spec-implementer should be 150 to preserve tier ordering |

**Steps**:

1. Open opencode.json and locate the agent definitions section (around line 100+).
2. Find agent.spec-implementer (currently around line 113).
3. Add a new line `"steps": 150,` to the spec-implementer object.
4. Ensure JSON syntax is correct (commas in the right places).
5. Verify that spec-implementer-lite remains at 120 to preserve tier ordering.

**Tests**:

- Validate opencode.json against schema.
- Confirm spec-implementer has `"steps": 150` and spec-implementer-lite has `"steps": 120`.

**Acceptance criteria covered**: Criterion 5 (add step budget to spec-implementer).

**Commit**: `chore(config): add steps budget to spec-implementer in opencode.json`

---

### Task 11: Create command shortcuts directory structure `[S]`

**Goal**: Create the `~/.config/opencode/command/` directory and the three command shortcut files (define.md, plan.md, implement.md) that route `/define`, `/plan`, and `/implement` commands to their respective agents.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `~/.config/opencode/command/define.md` | create | Routes /define to spec-definer agent |
| `~/.config/opencode/command/plan.md` | create | Routes /plan to spec-planner agent |
| `~/.config/opencode/command/implement.md` | create | Routes /implement to spec-implementer agent |

**Reuse**:

| File | What to reuse |
|------|---------------|
| Existing agent definitions (spec-definer.md, spec-planner.md, spec-implementer.md) | Agent names for routing |

**Steps**:

1. Create the directory `~/.config/opencode/command/` if it does not exist.
2. Create `define.md` with frontmatter `agent: spec-definer` and a brief description of what /define does (e.g., "Start a new spec definition").
3. Create `plan.md` with frontmatter `agent: spec-planner` and description (e.g., "Create an implementation plan from a spec").
4. Create `implement.md` with frontmatter `agent: spec-implementer` and description (e.g., "Implement a plan").
5. Each file should be minimal: frontmatter + 1–2 sentences describing the command's purpose.

**Tests**:

- Verify all three files exist in `~/.config/opencode/command/`.
- Confirm each file has valid YAML frontmatter with `agent:` key.
- Verify the agent names match existing agent definitions (spec-definer, spec-planner, spec-implementer).

**Acceptance criteria covered**: Criterion 6 (create command shortcuts).

**Commit**: `chore(commands): add /define, /plan, /implement shortcuts`

---

### Task 12: Verify all changes are usable in ~/.config/opencode/ `[S]`

**Goal**: Final verification that all modified and new files remain usable in ~/.config/opencode/ after being copied from the repo. Check schema validity, load success, no hardcoded secrets, and coherent workflows.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| All modified and new files from Tasks 1–11 | verify | Spot-check usability, schema validation, and workflow coherence |

**Steps**:

1. Verify opencode.json is valid JSON and passes schema validation (use opencode or a JSON validator).
2. Run a quick test to confirm agents and skills load without errors (e.g., `opencode run "list skills"` or similar).
3. Spot-check that no secrets are exposed in any file (baseURL is placeholder, no API keys, no endpoints).
4. Verify AGENTS.md is readable and makes sense as a global governance file.
5. Confirm command/*.md files are discoverable and have valid frontmatter.
6. Spot-check one workflow end-to-end: e.g., verify that hard rule #3 in spec-definer and spec-planner now match the Step 4/5 workflow described in the skills.
7. Document any issues or recommendations in the implementation report.

**Tests**:

- opencode.json validates against schema.
- Agents and skills load without errors.
- No secrets are exposed.
- One workflow (spec-define or spec-plan) reads coherently from hard rule through final status flip.
- All files are present and usable in ~/.config/opencode/.

**Acceptance criteria covered**: Criterion 7 (all changed files remain usable).

**Commit**: `chore(config): verify usability of Tier 1 changes in ~/.config/opencode`

---

**Task ordering**: Tasks 1–4 (hard rules and guidelines) are independent and can be done in parallel. Task 5 (AGENTS.md) is independent. Task 6 depends on Task 5. Tasks 7–8 (exploration delegation) are independent. Tasks 9–10 (opencode.json config) are independent. Task 11 (commands) is independent. Task 12 (final verification) depends on all prior tasks.

Recommended order to minimize risk: 1–4 (fix contradictions), 5–6 (add governance), 7–8 (delegate exploration), 9–10 (sanitize config), 11 (add commands), 12 (verify all).

## Edge Cases & Error Handling

- **Explore agent unavailable** (Tasks 7–8): If explore agent is not loaded or available during plan/implement, implementer should gracefully fall back to in-context glob/grep. Document the fallback in the skill and note it in the final report.

- **baseURL placeholder replacement** (Task 9): Spec says no secrets may be hardcoded; placeholder requires manual replacement before deployment. Document this clearly in the implementation report and in any README or setup guide.

- **Command file discovery** (Task 11): If opencode.json or opencode core does not auto-discover .md files in command/, command shortcuts may not work. Document any setup steps required in the report or update opencode.json registration if needed.

- **spec-implementer-lite step count preservation** (Task 10): Ensure spec-implementer-lite remains at `"steps": 120` to preserve tier ordering (lite is lower-spec agent). Verify in final validation.

- **AGENTS.md injection verification** (Task 6): After registering AGENTS.md in instructions, verify that it is actually injected into agent contexts by spot-checking a test run of one agent (e.g., `opencode run /define` with a toy request).

## Verification

1. **Validate opencode.json schema**: Use `opencode` or a JSON validator to confirm opencode.json is valid and complies with schema. No syntax errors, all required fields present.

2. **Load agents and skills**: Run `opencode run "list skills"` to confirm all agents (spec-definer, spec-planner, spec-implementer) and skills (spec-define, spec-plan, spec-implement) load without errors.

3. **Check for secrets**: Grep all modified files for exposed endpoints, API keys, or credentials. Confirm baseURL is a placeholder, not a live endpoint.

4. **Verify hard rule coherence**: Open spec-definer.md and spec-planner.md, and confirm hard rule #3 no longer contains the write-before-approval prohibition. Cross-check with corresponding skill files (spec-define/SKILL.md Step 4–5, spec-plan/SKILL.md Step 3–4) to ensure single narrative.

5. **Spot-check AGENTS.md injection**: Run a simple agent command (e.g., `opencode run /define "My new spec"`) in a sandbox and verify AGENTS.md rules are respected in the agent's output (concise, epistemologically honest, no speculative abstraction).

6. **Verify explore agent delegation**: Open spec-plan/SKILL.md and spec-implement/SKILL.md Step 2 and confirm they describe delegation to explore agent, not in-context glob/grep/read.

7. **Confirm command shortcuts exist**: Verify `~/.config/opencode/command/define.md`, `plan.md`, and `implement.md` exist and contain valid frontmatter (`agent:` key).

8. **Verify files are copy-safe**: Ensure no hardcoded paths, no secrets, and no dependencies on the git repo structure. All files should work identically when copied to a fresh ~/.config/opencode/ installation.

9. **Check tier ordering**: Confirm spec-implementer has `"steps": 150` and spec-implementer-lite has `"steps": 120` to preserve tier separation.

10. **Final coherence read**: Review the spec's Desired Outcome section and spot-check that each bullet is satisfied:
    - Single narrative for write-then-review? ✓ (Tasks 1–4)
    - Global AGENTS.md with rules? ✓ (Tasks 5–6)
    - Explore agent delegation? ✓ (Tasks 7–8)
    - Locked-down, templatable config? ✓ (Tasks 9–10)
    - Command shortcuts? ✓ (Task 11)
