#!/bin/bash
# Repo-wise backup of Claude Code chats, skills, and memory.
# Rerun anytime to refresh — rsync -a only adds/updates, never deletes locally.
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$DEST/chats" "$DEST/skills" "$DEST/memory" "$DEST/project-configs"

# 1. Chats — every project's raw transcripts (jsonl), grouped by clean repo/folder name
#    (not Claude Code's internal path-slug — see names.py).
shopt -s nullglob  # no projects yet = skip the loop instead of failing
for projdir in "$HOME/.claude/projects"/*/; do
  slug="$(basename "$projdir")"
  clean="$(python3 -c "import sys; sys.path.insert(0, '$DEST'); import names; print(names.resolve(sys.argv[1]))" "$slug")"
  mkdir -p "$DEST/chats/$clean"
  rsync -a --exclude='.DS_Store' "$projdir" "$DEST/chats/$clean/"
done
shopt -u nullglob

# 2. Global skills (skipped if you have none yet)
if [ -d "$HOME/.claude/skills" ]; then
  rsync -a --exclude='.DS_Store' "$HOME/.claude/skills/" "$DEST/skills/"
fi

# 3. Global memory (skipped if you have none yet)
if [ -d "$HOME/.claude/memory" ]; then
  rsync -a --exclude='.DS_Store' "$HOME/.claude/memory/" "$DEST/memory/"
fi

# 4. Project-scoped .claude configs (skills/rules/handoffs living inside individual repos).
#    Add your own repo paths here.
REPOS=(
  # "/path/to/your/repo"
)
for repo in ${REPOS[@]+"${REPOS[@]}"}; do  # this form survives an empty list on macOS bash 3.2
  if [ -d "$repo/.claude" ]; then
    name="$(basename "$repo")"
    mkdir -p "$DEST/project-configs/$name"
    rsync -a --exclude='.DS_Store' --exclude='settings.local.json' \
      "$repo/.claude/" "$DEST/project-configs/$name/.claude/"
  fi
done

# 5. Rebuild the chat index (session_id -> title -> repo/folder)
python3 "$DEST/index.py" rebuild "$DEST"

echo "Backup refreshed at: $DEST"
