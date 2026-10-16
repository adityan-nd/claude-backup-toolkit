#!/bin/bash
# Back up + push ALL memory files in one go — no arguments needed.
# Never deletes — rsync -a only adds/updates.
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$DEST/memory"
rsync -a --exclude='.DS_Store' "$HOME/.claude/memory/" "$DEST/memory/"

cd "$DEST"
git add memory
if git diff --cached --quiet; then
  echo "No memory changes — already up to date."
else
  git commit -m "Backup memory: full refresh" --quiet
  git push --quiet
  echo "Pushed full memory refresh."
fi
