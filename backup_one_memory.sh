#!/bin/bash
# Back up + push ONE memory file, as its own commit.
# Never deletes — removing it locally later leaves this backup copy untouched.
#
# Usage: ./backup_one_memory.sh <filename> [<filename> ...]
#   e.g. ./backup_one_memory.sh user-profile.md
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$HOME/.claude/memory"

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <filename> [<filename> ...]"
  exit 1
fi

for NAME in "$@"; do
  SRC="$SRC_ROOT/$NAME"
  if [ ! -e "$SRC" ]; then
    echo "Memory file '$NAME' not found under $SRC_ROOT — skipped."
    continue
  fi

  mkdir -p "$DEST/memory"
  cp "$SRC" "$DEST/memory/$NAME"

  cd "$DEST"
  git add "memory/$NAME"
  if git diff --cached --quiet; then
    echo "No changes for memory file '$NAME' — already up to date."
  else
    git commit -m "Backup memory: $NAME" --quiet
    git push --quiet
    echo "Pushed memory: $NAME"
  fi
  cd - > /dev/null
done
