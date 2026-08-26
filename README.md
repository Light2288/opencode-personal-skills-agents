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
├── specs/             # spec artifacts produced by the spec-define workflow
├── plans/             # implementation plans produced by the spec-plan workflow
└── install.sh         # idempotent sync into ~/.config/opencode
```

`specs/` and `plans/` are workflow output (the design record of how this
config was built out tier by tier). They are kept for history and are **not**
synced into `~/.config/opencode` — only `agents/`, `skills/`, `commands/`,
`AGENTS.md`, and `opencode.json` are installed.

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
| Skills  | `skills/code-review/`, `skills/debug/` |
| Agents  | `agents/review-quality.md`, `agents/review-spec.md` |
| Commands| `commands/review.md`, `commands/debug.md` |

### Tier 3 — Architecture layer

Codebase mapping, requirements analysis, and decision capture.

| Kind    | Files |
|---------|-------|
| Skills  | `skills/arch-map/`, `skills/arch-design/`, `skills/doc-analyze/` |
| Agents  | `agents/doc-analyst.md` |
| Commands| `commands/map.md`, `commands/analyze.md`, `commands/adr.md` |

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
