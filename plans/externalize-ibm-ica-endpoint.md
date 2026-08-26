# Plan: Externalize ibm-ica endpoint via {file:} and fix install/README inaccuracies

| Field        | Value                              |
|--------------|------------------------------------|
| **Title**    | Externalize ibm-ica endpoint via {file:} and fix install/README inaccuracies |
| **Spec**     | specs/externalize-ibm-ica-endpoint.md |
| **Type**     | bug                                |
| **Branch**   | fix/externalize-ibm-ica-endpoint   |
| **Created**  | 2026-08-27 00:52:18                |
| **Status**   | IMPLEMENTED                        |

## Context

Post-implementation amendments to the config-mirror repo. The ibm-ica endpoint
is currently kept out of the repo by an opaque `jq` re-injection in `install.sh`
that leaves a fresh install endpoint-less; and `README.md` documents that flow
plus two other inaccurate claims (an unverified prune-exemption asserted as
fact, and an over-strict command-directory claim). This changes the endpoint to
an explicit `{file:...}` reference, simplifies `install.sh` to a verbatim copy
with a non-fatal missing-file warning, and corrects the documentation.

## Branch Strategy

> **Before implementation, create a new branch from the repo's base
> branch.** The implementer auto-detects the base in this priority
> order: `develop` → `main` → `master` → `origin/HEAD`. Detected base here:
> `main` (no `develop`). Current branch is `fix/fix-command-routing`.
> The branch name is `fix/externalize-ibm-ica-endpoint`.
>
> Reference command (the implementer adapts to the detected base):
>
> ```bash
> git checkout main && git pull --ff-only && git checkout -b fix/externalize-ibm-ica-endpoint
> ```
>
> If the repo is not a git workspace, branch creation is skipped and
> noted in the implementation report.

Branch type mapping: bug → `fix/<slug>`.

## Commit Strategy

All commits follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Format: `<type>[(<scope>)]: <imperative description>`

One commit per task. Commits are prepared only if the user explicitly asks at
final review; otherwise changes are staged by explicit paths and left
uncommitted.

## Build & Test Commands

This is a config + shell + markdown repo. There is **no application test
runner and no red/green unit-test cycle.** Verification is mechanical:

| Action        | Command |
|---------------|---------|
| JSON validity | `python3 -c 'import json,sys; json.load(open("opencode.json"))'` (or `jq empty opencode.json`) |
| Shell syntax  | `bash -n install.sh` |
| Secret check | `jq -e '.provider["ibm-ica"].options.baseURL == "{file:~/.config/opencode/ibm-ica-baseurl}"' opencode.json` succeeds; plus a repo-wide `https?://` scan returning only the known-safe allowlist (`$schema`, opencode.ai docs, conventionalcommits.org). No real hostname handled. |
| Regression grep | `grep -rn "claude-opus-4-8" .` → expect zero |
| Warning smoke test | run `install.sh` with a temp `HOME` lacking `ibm-ica-baseurl` and confirm the warning fires and exit code is 0 |

## Tasks

### Task 1: Externalize baseURL in repo opencode.json `[S]`

**Goal**: Add a `provider.ibm-ica.options.baseURL` that references an external
untracked file, keeping any real endpoint out of the repo.

**Files**:

| File            | Action | Description |
|-----------------|--------|-------------|
| `opencode.json` | modify | Add `"options": { "baseURL": "{file:~/.config/opencode/ibm-ica-baseurl}" }` to `provider.ibm-ica`, placed before the `models` block (matching the live config's ordering). |

**Steps**:

1. Insert an `options` object into `provider.ibm-ica` with the single key
   `baseURL` set to the literal string `{file:~/.config/opencode/ibm-ica-baseurl}`.
2. Do NOT put any real URL anywhere. Keep 2-space indentation consistent with
   the file.

**Tests**:

- JSON parses (`python3 -c 'import json; json.load(open("opencode.json"))'`).
- `grep -n baseURL opencode.json` shows exactly the `{file:...}` literal.

**Acceptance criteria covered**: repo `opencode.json` has the `{file:...}`
baseURL and no real URL; JSON remains valid.

**Commit**: `fix(config): reference ibm-ica baseURL via {file:} instead of stripping it`

---

### Task 2: Simplify install.sh — verbatim copy + missing-file warning `[S]`

**Goal**: Remove the `jq` baseURL re-injection; copy `opencode.json` verbatim
with the same idempotent behavior as other files; warn non-fatally if the
external baseurl file is missing; drop `require jq`.

**Files**:

| File         | Action | Description |
|--------------|--------|-------------|
| `install.sh` | modify | Delete lines ~68–97 (the `src_cfg`/`dst_cfg`/`live_base_url`/`tmp_cfg` jq block). Replace with a verbatim rsync copy of `opencode.json` that only writes when changed (mirroring the `SYNC_FILES` loop at lines 61–66). Remove `require jq` (line 36). Add a post-sync guard checking `~/.config/opencode/ibm-ica-baseurl`. Update the top-of-file comment (lines 6–8) that references "never overwrites the live provider baseURL secret". |

**Reuse**:

| File         | What to reuse |
|--------------|---------------|
| `install.sh` | The existing `SYNC_FILES` rsync pattern (`rsync -a --out-format='%o %n'` + `log_change`) — simplest path is to add `opencode.json` to the `SYNC_FILES` array so it flows through the existing loop, removing the need for a bespoke block. |

**Steps**:

1. Add `opencode.json` to the `SYNC_FILES` array (line 19) so it is copied
   verbatim by the existing standalone-file loop with idempotent
   "only write if changed" semantics.
2. Delete the entire `--- opencode.json (preserve live baseURL secret) ---`
   block (lines 68–97), including the `tmp_cfg`/`trap` handling.
3. Remove `require jq` (line 36). Keep `require rsync`. (`jq` is used nowhere
   else — verified.)
4. Update the header comment (lines 6–8) to describe the new behavior
   (verbatim copy; warns if the external baseurl file is missing) instead of
   the old "never overwrites the live baseURL secret" language.
5. Before the final summary block, add a guard:
   ```bash
   if [ ! -f "${DEST}/ibm-ica-baseurl" ]; then
     echo "WARNING: ${DEST}/ibm-ica-baseurl not found. Create it with a single line containing your ibm-ica endpoint, or opencode calls will fail." >&2
   fi
   ```
   This must NOT change the exit code (warn, don't exit non-zero).

**Tests**:

- `bash -n install.sh` passes.
- `grep -n jq install.sh` → zero matches.
- Temp-HOME smoke test: run with `HOME` pointing at an empty temp dir (no
  `ibm-ica-baseurl`), confirm the WARNING line prints and exit code is 0.
- Idempotent re-run against a populated target prints "nothing changed".

**Acceptance criteria covered**: no jq re-injection; verbatim copy; non-fatal
missing-file warning; `require jq` removed.

**Commit**: `fix(install): copy opencode.json verbatim and warn on missing baseURL file`

---

### Task 3: Fix three README inaccuracies `[S]`

**Goal**: Correct the baseURL section, soften the pruning claim to an
unverified assumption, and correct the command-directory claim.

**Files**:

| File        | Action | Description |
|-------------|--------|-------------|
| `README.md` | modify | (a) Rewrite "opencode.json and the baseURL secret" (lines 88–94) to describe the `{file:...}` mechanism; remove all strip/re-inject/`jq` language. (b) Soften the pruning paragraph (lines 108–113) to an explicit unverified assumption. (c) Fix the command-discovery bullet (line 37) — plural canonical, singular back-compat. |

**Steps**:

1. **baseURL section**: Replace lines 88–94 with prose stating: the repo
   `opencode.json` references the endpoint via
   `{file:~/.config/opencode/ibm-ica-baseurl}`; the real endpoint lives only in
   that untracked local file (never committed); `install.sh` copies the config
   verbatim and prints a warning if the file is missing. Consider renaming the
   heading to reflect the `{file:...}` mechanism.
2. **pruning claim**: Replace the assertion (lines 108–113) with an explicit
   assumption, e.g.: "We keep `prune: true` on the assumption that loaded skill
   instructions survive pruning; this has not been independently verified
   against opencode source." (Confirmed with the user during define: it was not
   verified.)
3. **command-discovery bullet** (line 37): Change to state that plural
   `commands/` is canonical and preferred, and singular `command/` is accepted
   for backwards compatibility (per opencode docs). Remove "only discovers
   commands under that exact directory name".

**Tests**:

- `grep -in "jq\|re-inject\|strip" README.md` → no stale strip/jq language in
  the baseURL section.
- `grep -n "assumption\|not been independently verified" README.md` → present.
- `grep -n "backwards compatibility\|back-compat" README.md` → present in the
  command bullet.

**Acceptance criteria covered**: README baseURL section describes `{file:...}`;
pruning softened to assumption; command-dir claim corrected.

**Commit**: `docs(readme): document {file:} baseURL, soften prune claim, fix command-dir note`

---

### Task 4: Rewrite tier1 Post-Implementation Amendment baseURL note `[S]`

**Goal**: Update the tier1 amendment note to match the new `{file:...}` reality;
keep Status IMPLEMENTED.

**Files**:

| File                              | Action | Description |
|-----------------------------------|--------|-------------|
| `specs/opencode-tier1-fixes.md`   | modify | Rewrite the "Provider baseURL" bullet (line 85) under "Post-Implementation Amendments". Do NOT change the Status row (stays IMPLEMENTED). |

**Steps**:

1. Replace the line-85 bullet (currently: options block intentionally ABSENT,
   "no placeholder needed") with new framing: `provider.ibm-ica.options.baseURL`
   is present and references an external untracked file via
   `{file:~/.config/opencode/ibm-ica-baseurl}`; the real endpoint is never
   committed; `install.sh` warns (non-fatally) if the local file is missing on
   a fresh machine.
2. Leave the Status row and all other tier1 content untouched.

**Tests**:

- `grep -n "IMPLEMENTED" specs/opencode-tier1-fixes.md` → Status still
  IMPLEMENTED.
- `grep -n "file:" specs/opencode-tier1-fixes.md` → new note references the
  external file mechanism.

**Acceptance criteria covered**: tier1 amendment matches new reality; Status
still IMPLEMENTED.

**Commit**: `docs(spec): update tier1 baseURL amendment for {file:} externalization`

---

**Task ordering**: Task 1 (config) should land before Task 2 (install.sh) since
the install logic depends on the config now being copyable verbatim. Tasks 3
and 4 are documentation-only and independent of 1–2 and each other; they can be
done in any order after 1–2.

## Edge Cases & Error Handling

- **Missing `~/.config/opencode/ibm-ica-baseurl`**: `install.sh` prints a clear
  WARNING to stderr and exits 0 (Task 2). The file is user-supplied setup, not
  a script failure.
- **`{env:VAR}` alternative**: explicitly rejected in the spec — unreliable for
  the desktop app and silent-empty on unset. No code path uses it.
- **Related out-of-scope note**: `specs/fix-command-routing.md` (lines 19, 35,
  69) also references the old "absent baseURL block" framing. It is OUT OF
  SCOPE for this plan (only the tier1 amendment is in scope). Flagged for a
  possible future cleanup; not touched here.
- **Idempotency**: verbatim copy via the existing rsync loop preserves the
  "only write if changed" behavior; re-runs report "nothing changed".

## Verification

1. `python3 -c 'import json; json.load(open("opencode.json"))'` → exits 0
   (valid JSON); `grep -n baseURL opencode.json` shows only the `{file:...}`
   literal.
2. `bash -n install.sh` → exits 0; `grep -n jq install.sh` → zero matches.
3. Temp-HOME smoke test: `HOME="$(mktemp -d)" bash install.sh` (or equivalent)
   → WARNING about missing `ibm-ica-baseurl` prints and exit code is 0.
   (Clean up the temp dir afterward.)
4. `jq -e '.provider["ibm-ica"].options.baseURL == "{file:~/.config/opencode/ibm-ica-baseurl}"' opencode.json` succeeds, and a repo-wide `https?://` scan returns only the known-safe allowlist (`$schema`, opencode.ai docs, conventionalcommits.org). No real hostname is written into any repo file, including this plan.
5. `grep -rn "claude-opus-4-8" .` → zero occurrences.
6. README greps confirm: `{file:...}` described, pruning framed as assumption,
   command-dir corrected. Tier1 grep confirms Status IMPLEMENTED and the new
   `{file:...}` note.
7. Record each command and its actual output as the Step 5 proof lines in the
   implementation report.
