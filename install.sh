#!/usr/bin/env bash
#
# install.sh — sync this repo's opencode config into ~/.config/opencode.
#
# Idempotent: only files that actually changed are written, and a summary of
# what changed is printed. Never touches node_modules, package.json, or
# package-lock.json in the target. opencode.json is copied verbatim; its
# ibm-ica baseURL is externalized via {file:~/.config/opencode/ibm-ica-baseurl},
# so no endpoint secret lives in this repo. The script warns (non-fatally) if
# that external file is missing on the target.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.config/opencode"

# Directories synced 1:1 (with --delete so the target mirrors the repo).
SYNC_DIRS=(agents skills commands)

# Standalone files synced as-is (opencode.json is copied verbatim; its baseURL
# is externalized via {file:...}, so no re-injection is needed).
SYNC_FILES=(AGENTS.md opencode.json)

changed=0

log_change() {
  changed=1
  printf '  %s\n' "$1"
}

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: required command '$1' not found on PATH" >&2
    exit 1
  fi
}

require rsync

mkdir -p "$DEST"

echo "Syncing opencode config -> ${DEST}"

# --- directories ------------------------------------------------------------
# rsync reports each transferred path via --out-format; excludes keep runtime
# and OS cruft out of the target. --delete makes the target mirror the repo,
# but only within each synced directory (node_modules etc. live elsewhere).
for dir in "${SYNC_DIRS[@]}"; do
  src="${SCRIPT_DIR}/${dir}/"
  dst="${DEST}/${dir}/"
  mkdir -p "$dst"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    log_change "${dir}/: ${line}"
  done < <(rsync -a --delete \
    --exclude 'node_modules' \
    --exclude '.DS_Store' \
    --out-format='%o %n' \
    "$src" "$dst" | grep -v '/$' || true)
done

# --- standalone files -------------------------------------------------------
for file in "${SYNC_FILES[@]}"; do
  src="${SCRIPT_DIR}/${file}"
  dst="${DEST}/${file}"
  out="$(rsync -a --out-format='%o %n' "$src" "$dst")"
  [ -n "$out" ] && log_change "$file"
done

# --- baseURL file guard -----------------------------------------------------
# opencode.json references the ibm-ica endpoint via
# {file:~/.config/opencode/ibm-ica-baseurl}, which opencode reads at
# config-load time. The file is intentionally user-supplied and untracked, so
# a missing file is a setup step, not a script error: warn but do not fail.
if [ ! -f "${DEST}/ibm-ica-baseurl" ]; then
  echo "WARNING: ${DEST}/ibm-ica-baseurl not found. Create it with a single line containing your ibm-ica endpoint, or opencode calls will fail." >&2
fi

# --- summary ----------------------------------------------------------------
if [ "$changed" -eq 0 ]; then
  echo "Already up to date; nothing changed."
else
  echo "Done."
fi
