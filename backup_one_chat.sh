#!/bin/bash
# Back up + push ONE chat session, as its own commit.
# Never deletes anything — if you clear/delete the session locally afterward,
# this copy in the backup repo stays untouched (no --delete, no rm, ever).
#
# Usage: ./backup_one_chat.sh <session_id> [<session_id> ...]
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$HOME/.claude/projects"

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <session_id> [<session_id> ...]"
  exit 1
fi

for SID in "$@"; do
  found=0
  for projdir in "$SRC_ROOT"/*/; do
    slug="$(basename "$projdir")"
    if [ -f "${projdir}${SID}.jsonl" ]; then
      found=1
      clean="$(python3 -c "import sys; sys.path.insert(0, '$DEST'); import names; print(names.resolve(sys.argv[1]))" "$slug")"
      mkdir -p "$DEST/chats/$clean"
      cp "${projdir}${SID}.jsonl" "$DEST/chats/$clean/"
      if [ -d "${projdir}${SID}" ]; then
        mkdir -p "$DEST/chats/$clean/${SID}"
        rsync -a --exclude='.DS_Store' "${projdir}${SID}/" "$DEST/chats/$clean/${SID}/"
      fi

      title="$SID"
      if [ -f "${projdir}${SID}/custom-title.json" ]; then
        title="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('title','$SID'))" "${projdir}${SID}/custom-title.json" 2>/dev/null || echo "$SID")"
      fi
      cwd="$(python3 -c "
import json,sys
try:
    with open(sys.argv[1], errors='ignore') as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('cwd'):
                print(d['cwd']); break
except Exception:
    pass
" "${projdir}${SID}.jsonl" 2>/dev/null || echo "")"

      python3 "$DEST/index.py" upsert "$DEST" "$SID" "$title" "$clean" "$cwd"

      cd "$DEST"
      git add "chats/$clean/${SID}.jsonl" chats/INDEX.tsv chats/INDEX.md
      [ -d "chats/$clean/${SID}" ] && git add "chats/$clean/${SID}"
      if git diff --cached --quiet; then
        echo "No changes for $SID ($title) — already up to date."
      else
        git commit -m "Backup chat: $title ($SID)" --quiet
        git push --quiet
        echo "Pushed: $title ($SID)"
      fi
      cd - > /dev/null
    fi
  done
  if [ "$found" -eq 0 ]; then
    echo "Session $SID not found under $SRC_ROOT — skipped."
  fi
done
