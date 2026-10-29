#!/bin/bash
# Repo-wise backup of Claude Code chats, skills, and memory.
# Rerun anytime to refresh — rsync -a only adds/updates, never deletes locally.
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$DEST/chats" "$DEST/skills" "$DEST/memory" "$DEST/project-configs"

# 1. Chats — every project's raw transcripts (jsonl), grouped by clean repo/folder name
#    (not Claude Code's internal path-slug — see names.py).
#
#    Screenshots, PDFs and other attachments are inlined into transcripts as
#    base64 and are the bulk of their size; a browser- or simulator-heavy
#    session can pass GitHub's 100 MiB per-file limit and be rejected outright.
#    media.py stores each distinct blob once under
#    chats/<project>/<session>/media/ and leaves a reference behind, so
#    transcripts stay text. See docs/03-scripts.md.
python3 "$DEST/media.py" sync "$HOME/.claude/projects" "$DEST/chats"

# 2. Global skills (skipped if you have none yet)
if [ -d "$HOME/.claude/skills" ]; then
  rsync -a --exclude='.DS_Store' "$HOME/.claude/skills/" "$DEST/skills/"
fi

# 3. Global memory (skipped if you have none yet)
if [ -d "$HOME/.claude/memory" ]; then
  rsync -a --exclude='.DS_Store' "$HOME/.claude/memory/" "$DEST/memory/"
fi

# 3b. Global commands, and the prompts you typed across every session.
#     history.jsonl is the only record of those that lives outside the
#     transcripts, and it is small.
if [ -d "$HOME/.claude/commands" ]; then
  mkdir -p "$DEST/commands"
  rsync -a --exclude='.DS_Store' "$HOME/.claude/commands/" "$DEST/commands/"
fi
if [ -f "$HOME/.claude/history.jsonl" ]; then
  cp "$HOME/.claude/history.jsonl" "$DEST/prompt-history.jsonl"
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
