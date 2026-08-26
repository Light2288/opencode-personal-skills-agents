# Opencode Tier 2: Code Review and Debugging

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Opencode Tier 2: Code Review and Debugging             |
| **Type**      | chore                                                  |
| **Scope**     | ~/.config/opencode/ (skills, subagents, commands, workflows) |
| **Created**   | 2026-08-26 14:30:00                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

After Tier 1 establishes coherent workflows and governance, Tier 2 adds two critical capabilities that prevent defects from entering committed code and recover efficiently when tests fail unexpectedly.

**Code Review Gap**: spec-implement currently has no gate between "all tests pass" and "declare done." This allows:
- Spec violations (missing or extra work beyond acceptance criteria) to slip through.
- Quality issues (poor error handling, coupling, naming) that violate AGENTS.md rules to be built without judgment.
- Asymmetric cost: expensive Opus cycles spent implementing anti-YAGNI extras that should never exist.

**Debug Gap**: When a test fails unexpectedly in Step 4b (after code is written), spec-implement has no structured method. The implementer:
- Either guesses, risking patch symptoms instead of fixing root causes.
- Or escalates without evidence, wasting context.
- Silent failures happen if the implementer weakens tests to "pass."

**Commands Gap**: No quick shortcuts (/review, /debug) to invoke review/debug workflows outside spec-implement.

## Desired Outcome

After Tier 2 is complete:

1. **Code-review skill** with two subagents running in mandatory-order gate:
   - `review-spec` (Haiku/Sonnet, edit deny, mode subagent): checks diff against acceptance criteria; flags both missing requirements and YAGNI violations.
   - `review-quality` (GPT-5.6 Sol, edit deny, mode subagent): judges readability, duplication, error handling, coupling, naming; classifies issues as Important/Minor/Nitpick.
   - **Gate semantics**: spec compliance BEFORE quality. Quality runs only after spec review passes. If spec review finds issues, spec-implementer fixes them; spec review re-runs (quality review is discarded). Only after spec ✅ does quality run.

2. **Debug skill** (~80 lines, standalone):
   - Hard rule: name root cause WITH evidence before attempting any fix.
   - Method: reproduce deterministically → isolate via bisection → name cause → minimal fix + failing regression test.
   - Exit conditions: root cause named with evidence + regression test added (proceed to Step 4b.2) OR cannot name cause after bounded attempts (escalate, do not guess).
   - Invoked automatically and blocking from spec-implement Step 4b when a test failure is unexpected (not during red TDD phase); also available as `/debug` command for standalone use.

3. **Integration into spec-implement**:
   - Step 4b: Narrow trigger distinguishes TDD red (expected, proceed normally) from regression (unexpected, trigger debug).
   - Step 5.5 (new): Mandatory code-review gate before Step 5 (verify). Triggered by task risk tag: **mandatory** on L-risk tasks or tasks touching security/data/concurrency/migrations; **optional** (offered, not required) on S-risk tasks. M-risk tasks follow the spec-implementer-lite rule (escalate if present, handled by full implementer with mandatory review).
   - Step 5: Verification gate enforced: forbid declaring success without command + exit code + substantiating proof line (non-zero pass count or build artifact path).

4. **Command shortcuts**:
   - `/review`: Launch code-review on a provided diff (ad-hoc review, e.g., a pull request or pasted code).
   - `/debug`: Launch debug on a provided error message or failing test output (standalone debugging).
   - `/review` routes through `spec-implementer` for the review gate. Standalone `/debug` routes through the general-purpose `build` agent so it has no spec/plan assumptions; integrated Step 4b debugging remains in the implementer agent already running the workflow.

5. **Plan template update** (spec-plan skill):
   - Add risk field to task rows: `### Task N: <title> [S/M/L | risk: <none/security/data/concurrency/migrations>]`.
   - Risk is explicit, authored by planner, approved by user (never inferred by implementer).
   - Risk gates review; size is independent (effort estimate).

## Acceptance Criteria

- [ ] Create `~/.config/opencode/skills/code-review/SKILL.md` (~150 lines): documents workflow, two-subagent gate, spec-compliance-first rule, integration point in spec-implement Step 5.5, risk-based trigger logic.
- [ ] Create `agents/review-spec.md` (Haiku or Sonnet, mode subagent, edit deny) and `agents/review-quality.md` (GPT-5.6 Sol, mode subagent, edit deny) using the existing markdown-agent convention.
- [ ] `review-spec` checks diff against each acceptance criterion; produces a structured report: **PASS** (all criteria met, no extra work), **MISSING** (cite which criteria), **EXTRA** (cite YAGNI violations — work outside spec bounds).
- [ ] `review-quality` judges readability, duplication, error handling, coupling, naming; classifies each issue as Important/Minor/Nitpick; produces structured report with code locations and remedies.
- [ ] Gating rule: if `review-spec` is not PASS, its report is returned; `review-quality` is not run. If `review-spec` is PASS, `review-quality` runs and its report is returned. Both reports are passed to spec-implementer for decision (fix, appeal, or accept).
- [ ] Create `~/.config/opencode/skills/debug/SKILL.md` (~80 lines): four-phase method (reproduce → isolate → name → fix), hard rule on root-cause-first, exit conditions (success + regression test, or escalation), integration point in spec-implement Step 4b.
- [ ] Update `~/.config/opencode/skills/spec-implement/SKILL.md`:
  - Step 4b: define narrow trigger for unexpected failures (not TDD red phase); invoke debug skill automatically if triggered; block until root cause named or escalation decision made.
  - Step 5.5 (new, inserted before current Step 5): mandatory code-review gate. Reads task risk tag from plan; triggers review if task is L-risk or touches security/data/concurrency/migrations. Optional for S-risk (offered to user, not required).
  - Step 5: Verification gate — forbid success declaration without command + exit code + substantiating proof line (pass count or artifact). Phrase matches Step 6.5 to avoid drift.
  - Resequence subsequent steps (current Step 5 → Step 5a, Step 6 → Step 6, etc.) or renumber to accommodate new Step 5.5.
- [ ] Update `~/.config/opencode/skills/spec-plan/SKILL.md`: plan template now includes risk field per task. Risk is authored by planner, never inferred.
- [ ] Create `~/.config/opencode/commands/review.md`: frontmatter routes to spec-implementer; accepts diff and acceptance criteria; launches code-review workflow.
- [ ] Create `~/.config/opencode/commands/debug.md`: frontmatter routes to `build`; accepts error message or test output; launches the reusable debug workflow without assuming a spec or plan.
- [ ] Keep reviewer definitions out of opencode.json; register them through `agents/review-spec.md` and `agents/review-quality.md`. Discover code-review/debug skills and `/review`/`/debug` through their existing file conventions.

## Edge Cases & Error Handling

- **TDD vs. regression distinction**: Step 4a (red) intentionally produces failing tests. Step 4b's trigger must not fire during normal RED → GREEN cycle. Trigger narrowly on: (1) a previously-passing test now failing, (2) failure message indicates genuine mystery (not "assertion failed" in new test), (3) same failure after attempt 1 to fix. Document the heuristic in Step 4b so implementers understand when debug does/does not engage.
- **Review escalation**: If `review-spec` flags MISSING or EXTRA, spec-implementer returns the report and waits for user decision (fix code, fix plan, or override review). Do not auto-fix; the decision is not the implementer's to make.
- **Debug escalation**: If debug cannot name root cause after 3 bisection attempts or hypothesis cycles, it escalates to the user or full spec-implementer with evidence of what was tested and what was ruled out. Do not guess; never proceed on anonymous failure.
- **Risk tag missing**: If planner omits risk tag, spec-implement conservatively treats task as M-risk (escalate if present; full implementer can proceed with mandatory review). Warn user during plan review.
- **S-risk optional review declined**: If user declines optional review on S-risk task, spec-implementer proceeds without code-review. Log this decision for auditability.
- **Standalone /debug without spec context**: `/debug` command may be used outside spec-implement. Must be able to accept a pasted error/test output with no plan context. Still applies the four-phase method and hard root-cause-first rule; exit condition is either "root cause named with evidence" (user fixes manually) or "escalated" (return evidence to user). Do not attempt fix without spec context — that's spec-implementer's domain.
- **Standalone /review without spec**: `/review` command accepts diff and acceptance criteria as text input. Runs both review subagents sequentially (not gated to spec context). Output is advisory (no mandatory fix cycle), used for ad-hoc code review (PRs, design review, linting).

## Dependencies & Constraints

- **Subagent availability**: Both reviewer markdown agent files must be installed and discoverable before code-review is invoked. If unavailable, code-review fails with a clear error (do not silently skip review).
- **Model assignments**: review-spec uses Haiku or Sonnet (cost control); review-quality uses GPT-5.6 Sol (complex judgment). These assignments are locked and not overridable by spec-implementer.
- **Edit-deny mode requirement**: Both subagents must run in mode: subagent with edit: deny. This prevents the reviewers from making fixes; they report findings only. Fixes are spec-implementer's responsibility.
- **spec-implement integration**: Tier 2 changes to spec-implement depend on Tier 1 being complete (spec-implement structure, AGENTS.md rules, explore agent delegation). Verify Tier 1 status before starting Tier 2 implementation.
- **Plan template breaking change**: Adding risk field to spec-plan template is a breaking change. Existing plans (from before Tier 2) will not have risk field. Spec-implementer must gracefully handle missing risk field (treat as M-risk, escalate if present) and warn user.
- **Token economy**: Code-review Step 5.5 uses Haiku (spec) + GPT-5.6 Sol (quality) tokens every time it runs. Mandatory review on L-risk tasks is acceptable cost; optional on S-risk is user's choice. Full-session token budget (Step 1 in opencode.json) must accommodate this; verify during implementation (estimate ~20-30k tokens per review cycle).

## Out of Scope

- **Tier 1**: Config, governance, exploration agent, commands infrastructure. Assumed complete.
- **Tier 3**: Architecture agents, codebase refactoring, cross-cutting concerns.
- **Auto-fixing**: Reviewers never auto-fix; they report and spec-implementer (or user in /review mode) makes the fix decision.
- **Custom review criteria**: review-spec judgment is hard-wired against acceptance criteria. Custom linting rules, style guides, or tool integrations are out of scope.
- **Integration with external tools**: No PR review system, CI/CD pipeline, or third-party code review tool integration. Standalone commands only.
- **Persistent review state**: Review reports are ephemeral; no database of past reviews or audit trail (beyond chat history).

## Notes

- **Slug**: `opencode-tier2-quality` (confirmed).
- **Terminology**: "Risk tag" is separate from "size tag" (S/M/L). Both are authored at plan time. Size estimates effort; risk gates review.
- **Gate analogy**: The code-review gate (Step 5.5) is similar to the spec-compliance gate in debug (root cause first): you must understand the problem (spec compliance, root cause) before attempting a solution (quality polish, fix).
- **Sequential detail**: Code-review runs review-spec, waits for result, then conditionally runs review-quality. Within each run, subagents operate in their own contexts (edit deny, isolated judgment). They do not call each other or read each other's outputs.
- **Tier 2 readiness**: This spec assumes Tier 1 is IMPLEMENTED. If Tier 1 is still DRAFT or DEFINED, coordinate timing or mark this spec as blocked.
- **Directory structure**: After Tier 2:
  - `~/.config/opencode/skills/code-review/SKILL.md` (new)
  - `~/.config/opencode/skills/debug/SKILL.md` (new)
  - `~/.config/opencode/commands/review.md` (new)
  - `~/.config/opencode/commands/debug.md` (new)
  - New: `~/.config/opencode/agents/review-spec.md`, `~/.config/opencode/agents/review-quality.md`
  - Modified: `~/.config/opencode/skills/spec-implement/SKILL.md`, `~/.config/opencode/skills/spec-plan/SKILL.md`, `opencode.json`
- **Testing Tier 2**: After implementation, verify:
  - Run a spec-implement task marked L-risk; code-review Step 5.5 is triggered automatically.
  - Introduce a code quality issue (e.g., unused variable); review-quality flags it as Minor.
  - Introduce a YAGNI extra in the diff; review-spec flags it as EXTRA.
  - Pause spec-implement's Step 4b with a mysterious test failure; debug skill runs, names root cause, adds regression test, resumes.
  - Use `/review` command on a pasted code snippet; both review subagents run.
  - Use `/debug` command on a pasted error; debug skill runs without spec context.
