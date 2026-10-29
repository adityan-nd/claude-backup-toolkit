#!/bin/bash
# One command: refresh the backup, check it for secrets, commit, push.
#
#   ./backup.sh                        everything, then commit + push
#   ./backup.sh --no-push              commit locally, review before pushing
#   ./backup.sh --force                re-extract every transcript (after upgrading)
#   ./backup.sh --with-shell-history   also back up ~/.zsh_history (see below)
#
# backup_claude.sh does the copying; this wraps it with the secret gate, the
# commit and the push, so a routine backup is one command and no arguments.
# Nothing is committed if scan_secrets.py finds anything.
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUSH=1
FORCE=0
SHELL_HISTORY=0
for arg in "$@"; do
  case "$arg" in
    --no-push) PUSH=0 ;;
    --force) FORCE=1 ;;
    --with-shell-history) SHELL_HISTORY=1 ;;
    -h|--help) sed -n '2,10p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

# Transcripts are append-only, so media.py skips any whose backup copy is
# newer than the source. After upgrading the toolkit that shortcut hides
# transcripts copied by an older version, so --force clears it.
if [ "$FORCE" -eq 1 ]; then
  find "$DEST/chats" -name '*.jsonl' -exec touch -t 197001020000 {} + 2>/dev/null || true
fi

"$DEST/backup_claude.sh"

# Your own shell history. OFF by default: people paste tokens into commands,
# and scan_secrets.py's five patterns will not catch most of them. Everything
# Claude ran is already in the transcripts regardless.
if [ "$SHELL_HISTORY" -eq 1 ]; then
  mkdir -p "$DEST/shell-history"
  for h in "$HOME/.zsh_history" "$HOME/.bash_history"; do
    [ -f "$h" ] && cp "$h" "$DEST/shell-history/$(basename "$h")"
  done
  echo "    shell history included - review it before pushing"
fi

echo "==> Scanning for secrets"
if ! python3 "$DEST/scan_secrets.py" "$DEST"; then
  echo
  echo "Possible secrets found (above). NOTHING was committed or pushed."
  echo "Open each file and check. If a key is real: rotate it, then remove it"
  echo "here AND from the matching file under ~/.claude/projects/, or the next"
  echo "backup copies it straight back. Then run ./backup.sh again."
  exit 1
fi

cd "$DEST"
git add -A
if git diff --cached --quiet; then
  echo "==> Nothing changed since the last backup."
  exit 0
fi

files=$(git diff --cached --name-only | wc -l | tr -d ' ')
git commit -q -m "Backup: $files files updated

$(git diff --cached --shortstat)"

if [ "$PUSH" -eq 0 ]; then
  echo "==> Committed locally ($files files). Not pushed (--no-push)."
  echo "    Push when ready:  git -C \"$DEST\" push"
  exit 0
fi

git push --quiet
echo "==> Pushed. $files files updated."
