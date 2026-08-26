# Externalize ibm-ica endpoint via {file:} and fix install/README inaccuracies

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | Externalize ibm-ica endpoint via {file:} and fix install/README inaccuracies |
| **Type**      | bug                                                    |
| **Scope**     | opencode-personal-skills-agents repo (opencode.json, install.sh, README.md, tier1 spec) |
| **Created**   | 2026-08-27 00:50:40                                    |
| **Status**    | IMPLEMENTED                                            |

## Problem Statement

Post-implementation amendments to the config-mirror repo. Four issues remain
after the initial repo scaffolding (`.gitignore`, `README.md`, `install.sh`,
and the `command/` → `commands/` rename):

1. **Endpoint handling is fragile and secret-coupled.** The repo's
   `opencode.json` has no `provider.ibm-ica.options` block, and `install.sh`
   re-injects the live `baseURL` via `jq` at sync time. This means a fresh
   install produces a config with no endpoint, and the mechanism is opaque
   dead complexity. opencode supports `{file:path}` substitution inside
   `provider.<id>.options` (docs show `apiKey: "{file:~/.secrets/openai-key}"`),
   so the endpoint can be referenced from an untracked local file instead —
   keeping the real endpoint out of the repo while making a fresh install
   functional once that file exists.

   `{env:VAR}` is rejected: the user runs the **desktop app**, and a shell
   `export` in `.zshrc` is not reliably visible to a GUI-launched process.
   Also, an unset `{env:VAR}` silently resolves to an empty string (silent
   failure). `{file:...}` is read by opencode at config-load time regardless
   of launch method, so it is the correct mechanism here.

2. **README documents the wrong endpoint mechanism.** The "opencode.json and
   the baseURL secret" section describes the strip-and-`jq`-re-inject flow,
   which will no longer exist.

3. **README asserts an unverified pruning claim as fact.** It states opencode
   "protects the `skill` tool output from pruning" and that skill instructions
   are "exempt from compaction pruning." This was not verified against opencode
   source or docs (the opencode docs describe `prune` only as "Remove old tool
   outputs to save tokens", with no skill exemption; the tier1 spec/plan only
   said to "verify during implementation" and recorded no result). Asserting it
   as fact violates the AGENTS.md epistemic-honesty rule.

4. **README states an incorrect command-discovery claim.** It says opencode
   "only discovers commands under that exact directory name" (plural
   `commands/`). Per opencode docs, singular `command/` is also supported for
   backwards compatibility; plural is canonical/preferred, not exclusive.

## Current Behavior

- `opencode.json` (repo) has no `provider.ibm-ica.options` block; the endpoint
  is absent from the repo entirely.
- `install.sh` reads the live `provider["ibm-ica"].options.baseURL` from the
  target config and re-injects it into the copied config via `jq`; `jq` is a
  hard-required dependency; the script warns nothing about a missing endpoint
  because it always sources one from the existing target.
- `README.md` "opencode.json and the baseURL secret" section describes the
  strip/re-inject flow.
- `README.md` states the skill-prune-exemption as verified fact.
- `README.md` states plural `commands/` is the only discovered directory name.

## Desired Outcome

1. **opencode.json (repo)** carries an explicit externalized reference:
   ```json
   "options": { "baseURL": "{file:~/.config/opencode/ibm-ica-baseurl}" }
   ```
   No real endpoint appears anywhere in the repo. The config remains valid JSON.

2. **install.sh** copies `opencode.json` verbatim (same idempotent
   "only write if changed" behavior as the other synced files) with no `jq`
   re-injection. After syncing, if `~/.config/opencode/ibm-ica-baseurl` does
   not exist, it prints a clear, non-fatal warning telling the user to create
   the file. The `require jq` check is removed if nothing else uses `jq`.

3. **README.md** is corrected on three points:
   - baseURL section rewritten to describe the `{file:...}` mechanism (config
     references the endpoint via `{file:~/.config/opencode/ibm-ica-baseurl}`;
     the real endpoint lives only in that untracked local file; `install.sh`
     copies the config verbatim and warns if the file is missing). All
     strip/re-inject/`jq` language removed.
   - pruning claim softened to an explicit, unverified assumption (not
     independently verified against opencode source).
   - command-discovery claim corrected: plural `commands/` is canonical and
     preferred; singular `command/` is accepted for backwards compatibility.

4. **specs/opencode-tier1-fixes.md** "Post-Implementation Amendments" baseURL
   note rewritten: the `options.baseURL` is now present and references an
   external untracked file via `{file:...}`; the real endpoint is never
   committed; `install.sh` warns if the local file is missing on a fresh
   machine. Status stays `IMPLEMENTED`.

## Acceptance Criteria

- [ ] Repo `opencode.json` has `provider.ibm-ica.options.baseURL` equal to
      `"{file:~/.config/opencode/ibm-ica-baseurl}"` and contains NO real URL
      anywhere.
- [ ] `opencode.json` remains valid JSON.
- [ ] `install.sh` no longer contains the `jq` baseURL re-injection block;
      copies `opencode.json` verbatim; warns (non-fatally, exit 0) if
      `~/.config/opencode/ibm-ica-baseurl` is absent; `require jq` removed if
      `jq` is otherwise unused.
- [ ] README baseURL section describes the `{file:...}` mechanism; the pruning
      claim is softened to a stated, unverified assumption; the
      commands-directory claim is corrected (plural canonical, singular
      back-compat).
- [ ] Tier 1 amendment note matches the new `{file:...}` reality; Status
      still `IMPLEMENTED`.
- [ ] `jq -e '.provider["ibm-ica"].options.baseURL == "{file:~/.config/opencode/ibm-ica-baseurl}"' opencode.json` succeeds (proves the placeholder is exactly in place and no real URL is in the config), AND a repo-wide scan for `https?://` URLs returns only the known-safe allowlist (`$schema`, opencode.ai docs, conventionalcommits.org); any other URL is surfaced for human review. No real hostname is needed or handled.
- [ ] Zero occurrences of `claude-opus-4-8` in the repo (regression guard).
- [ ] Verification records each command + result as Step 5 proof.

## Edge Cases & Error Handling

- **`ibm-ica-baseurl` file missing on fresh machine**: `install.sh` prints a
  clear warning and exits 0 (the file is intentionally user-supplied; a
  missing file is a setup step, not a script failure).
- **`{env:VAR}` alternative**: explicitly rejected — unreliable for the
  desktop app and silent-empty on unset. `{file:...}` chosen instead.
- **Existing target `opencode.json` differs**: script overwrites verbatim only
  when content differs (idempotent no-op when identical).

## Dependencies & Constraints

- This is config + shell + markdown, **not** an application with a test
  runner. There is no unit-test red/green cycle. Verification is:
  JSON parses; grep proves no real endpoint and no `claude-opus-4-8` in the
  repo; `install.sh` passes `bash -n`; optional dry-run in a temp `HOME` to
  confirm the missing-file warning fires. Each command + output is recorded
  as the Step 5 proof line.
- Verified facts (confirmed against opencode docs on 2026-08-27):
  - `{env:VAR}` and `{file:path}` substitution are supported, including inside
    `provider.<id>.options`.
  - Unset `{env:VAR}` resolves to an empty string.
  - Singular `command/` is supported for backwards compatibility; plural
    `commands/` is canonical/preferred.
- The prune-exemption behavior is **not** verified; README must frame it as an
  assumption.

## Out of Scope

- The `command/` → `commands/` rename and the `.DS_Store`/`.gitignore` fix are
  already correct and must NOT be re-touched. (Recorded here for context only:
  the rename is complete and `.DS_Store` is already gitignored.)
- `references/` extraction and git base-branch dedup (separate future spec).
- Any change to skills, agents, or command bodies.
- Reverting any `Status` row on existing tier specs (these are
  post-implementation amendments; tier statuses stay `IMPLEMENTED`).

## Notes

- Confirmed with the user during define: the skill-output-prune-exemption was
  **not** verified against opencode source; README will state it as an
  explicit unverified assumption.
- Staging is by explicit paths; do not commit unless the user explicitly asks
  at final review.
