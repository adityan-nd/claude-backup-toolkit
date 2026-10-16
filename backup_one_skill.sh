#!/bin/bash
# Back up + push ONE skill, as its own commit.
# Never deletes — removing/renaming it locally later leaves this backup copy untouched.
#
# Usage: ./backup_one_skill.sh <skill-name> [<skill-name> ...]
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$HOME/.claude/skills"

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <skill-name> [<skill-name> ...]"
  exit 1
fi

for NAME in "$@"; do
  SRC="$SRC_ROOT/$NAME"
  if [ ! -e "$SRC" ]; then
    echo "Skill '$NAME' not found under $SRC_ROOT — skipped."
    continue
  fi

  mkdir -p "$DEST/skills/$NAME"
  rsync -a --exclude='.DS_Store' "$SRC/" "$DEST/skills/$NAME/"

  cd "$DEST"
  git add "skills/$NAME"
  if git diff --cached --quiet; then
    echo "No changes for skill '$NAME' — already up to date."
  else
    git commit -m "Backup skill: $NAME" --quiet
    git push --quiet
    echo "Pushed skill: $NAME"
  fi
  cd - > /dev/null
done
