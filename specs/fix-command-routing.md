# Fix command routing and stale Tier 1 spec references

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Fix command routing and stale Tier 1 spec references   |
| **Type**      | bug                                                    |
| **Scope**     | OpenCode commands, config, and implemented tier specs  |
| **Created**   | 2026-08-27 00:09:55                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

Four command entry points are hosted by unsuitable agents, causing runtime failures or contradicting their declared behavior. Three architecture/document commands inherit whichever agent is active and can therefore lack required tools; `/review` is hosted by an edit-enabled spec agent despite declaring advisory read-only behavior. Two statements in the implemented Tier 1 spec also no longer describe the delivered `opencode.json`.

## Current Behavior

- `command/map.md`, `command/analyze.md`, and `command/adr.md` omit `agent:` frontmatter, so they inherit the active agent. Restricted agents may deny the bash, edit, or task operations their skills require.
- `command/review.md` routes through `spec-implementer`, although its body declares advisory read-only mode and its actual reviewers are read-only subagents.
- `specs/opencode-tier1-fixes.md` says the provider `baseURL` was sanitized to `<YOUR_PROVIDER_BASE_URL>`, but the repository config intentionally contains no provider `options` or `baseURL` block.
- The Tier 1 spec says `title`, `summary`, and `scout` route to Haiku. The repository config explicitly routes only `explore` and `general`; `small_model` is Haiku, and this OpenCode version supports explicit `title` and `summary` overrides. `scout` is experimental and is not available in the installed runtime.

## Desired Outcome

- Every command file declares its host agent, with `/map`, `/analyze`, `/adr`, and `/review` routed to `build`.
- The command bodies remain byte-for-byte unchanged apart from frontmatter `agent:` fields.
- `opencode.json` explicitly routes the valid built-in `title` and `summary` agents to `ibm-ica/claude-haiku-4-5`.
- The implemented Tier 1 and Tier 2 specs retain `IMPLEMENTED` status and include post-implementation amendment notes that accurately record the delivered configuration and routing decisions.

## Acceptance Criteria

- [ ] Every Markdown file directly under `command/` has an `agent:` frontmatter field.
- [ ] `command/map.md`, `command/analyze.md`, `command/adr.md`, and `command/review.md` route to `build`; their command bodies are otherwise unchanged.
- [ ] The resolved `build` agent allows bash, edit, and task.
- [ ] `opencode.json` remains valid JSON and explicitly routes `title` and `summary` to `ibm-ica/claude-haiku-4-5`.
- [ ] `specs/opencode-tier1-fixes.md` retains `IMPLEMENTED` status and has a `Post-Implementation Amendments` note explaining that the absent `baseURL` block is the sanitized, secret-free delivered state, that title/summary are explicitly routed to Haiku, and that scout routing is inapplicable because no scout agent is available in this OpenCode installation.
- [ ] `specs/opencode-tier2-quality.md` retains `IMPLEMENTED` status and has a `Post-Implementation Amendments` note recording the `/review` host-agent change from `spec-implementer` to `build` and its rationale.
- [ ] The repository contains zero occurrences of the forbidden Claude Opus 4.8 model ID.
- [ ] Verification records each command, exit code, and a substantiating output line; no unit-test red/green cycle is required because this repository change consists only of Markdown and JSON configuration edits and has no applicable test runner.
- [ ] Only the specified command frontmatter, `opencode.json` title/summary routing, the two tier-spec amendment notes, and this workflow's spec/plan status files are changed and explicitly staged.

## Edge Cases & Error Handling

- **Restricted invoking agent**: Command-level `agent: build` must replace the active restricted agent so required bash, edit, and task tools are available.
- **Invalid agent key**: Do not add `scout` to `opencode.json`; the installed OpenCode 1.15.4 runtime does not expose it without an experimental flag.
- **Inherited model ambiguity**: Add explicit `title` and `summary` model overrides even though title otherwise falls back to the Haiku `small_model`, making the Tier 1 routing claim directly visible and stable in the repository config.
- **Historical status preservation**: Do not revert either tier spec's `IMPLEMENTED` status while appending amendments.
- **Merged external config**: Validate the repository's `opencode.json` directly for JSON correctness and forbidden model references; resolved user-level config may contain unrelated values not present in this repository.

## Dependencies & Constraints

This is an OpenCode configuration and Markdown correction, not an application-code project. There is no unit test suite or meaningful TDD red/green cycle. Verification consists of checking command frontmatter coverage and routing, parsing `opencode.json`, inspecting resolved build-agent permissions, checking for zero repository occurrences of the forbidden Claude Opus 4.8 model ID, and comparing the Tier 1 amendment against `opencode.json`.

OpenCode 1.15.4's published schema accepts `title` and `summary` under `agent`. Its source applies an explicit `agent.title.model` before falling back to `small_model`; `scout` is conditionally registered only when its experimental runtime flag is enabled. `opencode debug agent build` confirms the resolved build agent exposes bash, edit, and task.

Stage changes with explicit paths. Do not commit without explicit user approval at final review.

## Out of Scope

- References extraction or git base-branch deduplication.
- `.DS_Store` or `.gitignore` hygiene.
- Command-body changes.
- Skill logic changes.
- Agent prompt changes.
- Any agent configuration beyond the requested command hosts and explicit title/summary Haiku routing.

## Notes

- The slug is `fix-command-routing`.
- The Tier 1 baseURL discrepancy is resolved as a documentation amendment: omitting the entire provider options block is the delivered secret-free state and does not require a placeholder.
- Step 5 proof must include commands and results for command `agent:` coverage, JSON parsing, forbidden-model absence, and Tier 1/config consistency.
