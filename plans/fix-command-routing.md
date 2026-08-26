# Plan: Fix command routing and stale Tier 1 spec references

| Field        | Value                              |
|--------------|------------------------------------|
| **Title**    | Fix command routing and stale Tier 1 spec references |
| **Spec**     | specs/fix-command-routing.md       |
| **Type**     | bug                                |
| **Branch**   | fix/fix-command-routing            |
| **Created**  | 2026-08-27 00:09:55                |
| **Status**   | IMPLEMENTED                        |

## Context

Three commands currently inherit a potentially restricted active agent, and `/review` uses an edit-enabled spec host despite its advisory mode. The implemented Tier 1 and Tier 2 specs also need amendments so their historical claims match the delivered command routing and `opencode.json` without changing their `IMPLEMENTED` statuses.

## Branch Strategy

Use `main` as the detected base and `fix/fix-command-routing` as the implementation branch. Because the approved spec and this plan are created uncommitted in the current session, create the branch without pulling or switching away so these workflow files follow safely into implementation.

## Commit Strategy

No commits will be created unless the user explicitly requests one at final review. If requested, use Conventional Commits and combine the tightly related config correction into `fix(config): correct command routing and tier specs`.

## Build & Test Commands

This repository has no application manifest, build step, or unit-test runner. TDD red/green does not apply to these Markdown and JSON config edits. Use the verification commands in the final section and record each command's exit code and proof output.

## Tasks

### Task 1: Pin command host agents `[S | risk: none]`

**Goal**: Ensure all command entry points run under an explicitly suitable host.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `command/map.md` | modify | Add `agent: build` to frontmatter only. |
| `command/analyze.md` | modify | Add `agent: build` to frontmatter only. |
| `command/adr.md` | modify | Add `agent: build` to frontmatter only. |
| `command/review.md` | modify | Replace `agent: spec-implementer` with `agent: build`. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `command/debug.md` | Existing `agent: build` frontmatter convention. |

**Steps**:

1. Add or replace only the command frontmatter `agent:` field.
2. Confirm each command body below the closing frontmatter delimiter is unchanged.
3. Inspect `opencode debug agent build` to confirm bash, edit, and task tools are enabled.

**Tests**:

- Count command files and `agent:` frontmatter fields and require equal counts.
- Check the four corrected commands each contain `agent: build`.
- Inspect the resolved build agent's tools for bash, edit, and task set to true.

**Acceptance criteria covered**: 1, 2, 3.

---

### Task 2: Complete valid Haiku routing `[S | risk: none]`

**Goal**: Make Tier 1's valid title/summary Haiku-routing claim explicit in repository config.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `opencode.json` | modify | Add `title` and `summary` agent model overrides using `ibm-ica/claude-haiku-4-5`. |

**Reuse**:

| File | What to reuse |
|------|---------------|
| `opencode.json` | Existing `explore` and `general` model override shape. |

**Steps**:

1. Add `title` and `summary` entries to the existing `agent` object with the same Haiku model value as `explore` and `general`.
2. Do not add `scout`; OpenCode 1.15.4 registers it only behind an experimental runtime flag and the installed agent output does not expose it.
3. Parse the file as strict JSON and inspect resolved title/summary agents to confirm the explicit override is honored.

**Tests**:

- Parse `opencode.json` with a JSON parser.
- Assert `agent.title.model` and `agent.summary.model` both equal `ibm-ica/claude-haiku-4-5`.
- Confirm `opencode debug agent title` and `opencode debug agent summary` report that model after the edit.

**Acceptance criteria covered**: 4.

---

### Task 3: Amend implemented tier specs `[S | risk: none]`

**Goal**: Preserve historical implementation statuses while documenting the delivered decisions accurately.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `specs/opencode-tier1-fixes.md` | modify | Append post-implementation amendments for omitted baseURL, title/summary routing, and unavailable scout. |
| `specs/opencode-tier2-quality.md` | modify | Append post-implementation amendment for `/review` host routing. |

**Steps**:

1. Append a `Post-Implementation Amendments` section to Tier 1 explaining that omission of the provider options/baseURL block is the secret-free delivered state, title/summary are explicitly routed to Haiku, and scout is unavailable in this installation.
2. Append a matching section to Tier 2 recording that `/review` now uses `build` because the host is ad hoc and the actual reviewers remain edit-denied subagents.
3. Confirm both existing `Status` rows remain `IMPLEMENTED`.
4. Compare the Tier 1 amendment statements directly with `opencode.json` and installed agent output.

**Tests**:

- Search both tier specs for exactly one `Post-Implementation Amendments` heading.
- Check both status rows still contain `IMPLEMENTED`.
- Verify Tier 1 amendment claims against absence of `baseURL`, explicit title/summary Haiku values, and absent scout entry in `opencode.json`.

**Acceptance criteria covered**: 5, 6.

---

### Task 4: Verify and stage the correction `[S | risk: none]`

**Goal**: Produce Step 5 evidence for every config acceptance criterion and stage only intended paths.

**Files**:

| File | Action | Description |
|------|--------|-------------|
| `specs/fix-command-routing.md` | modify | Set workflow status to `IMPLEMENTED` after verification. |
| `plans/fix-command-routing.md` | modify | Set workflow status to `IMPLEMENTED` after verification. |

**Steps**:

1. Run all commands in Verification and record command, exit code, and proof output in the implementation report.
2. Inspect the final diff for scope and command-body preservation.
3. Update this spec and plan to `IMPLEMENTED` only after all checks pass.
4. Stage the nine intended paths explicitly; never use `git add .` or `git add -A`.
5. Stop at final review without committing.

**Tests**:

- All verification commands must exit 0.
- `git diff --cached --name-only` must list only the intended files.

**Acceptance criteria covered**: 7, 8, 9.

**Task ordering**: Tasks 1, 2, and 3 are independent config/documentation edits. Task 4 depends on all three and is the only staging step. Step 5.5 review is optional because every task is S-sized with `risk: none`.

## Edge Cases & Error Handling

- A command invoked from a restricted primary agent is switched to `build` by explicit command frontmatter (Task 1).
- The merged user config may include stale values absent from this repository; repository-wide regression checks operate on tracked workspace content, not unrelated global config (Task 4).
- Explicit title/summary overrides are used even though title can fall back to `small_model`, making the intended routing independently inspectable (Task 2).
- No `scout` override is added while that agent is unavailable in the installed runtime (Tasks 2 and 3).
- Tier spec statuses are never moved backward from `IMPLEMENTED` (Task 3).

## Verification

1. Command coverage and routing: run a shell loop over `command/*.md` that fails if any file lacks a frontmatter `agent:` field or if map/analyze/adr/review do not use `build`; print counts and corrected routes as proof.
2. JSON validity and routing: parse `opencode.json` with `node -e`, assert title and summary model values, and print `JSON valid; title/summary=ibm-ica/claude-haiku-4-5`.
3. Build permissions: run `opencode debug agent build`, assert its tool map enables bash, edit/apply_patch, and task, and print `build tools: bash=true edit=true task=true`.
4. Regression guard: search the repository for the forbidden Claude Opus 4.8 model ID, invert the match status, and print a zero-occurrence proof line. Supply the exact model ID to the command without recording that literal in a repository file.
5. Tier consistency: parse `opencode.json` and inspect `specs/opencode-tier1-fixes.md` to assert no repository baseURL, explicit title/summary Haiku routing, no scout entry, amendment coverage, and retained `IMPLEMENTED` status; print one summary line.
6. Tier 2 consistency: assert the amendment mentions `/review`, `build`, and the prior `spec-implementer` host while retaining `IMPLEMENTED`; print one summary line.
7. Diff scope: inspect `git diff --check`, `git diff`, and staged path names; confirm command bodies have no changes beyond frontmatter.
