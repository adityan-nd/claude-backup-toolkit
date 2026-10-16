#!/bin/bash
# One-command setup. Creates your own backup folder from this toolkit, connects
# it to a NEW private GitHub repo of yours, runs the first backup, and pushes it.
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/adityan-nd/claude-backup-toolkit/main/install.sh)
#
# Optional arguments: [folder] [github-repo-name]
#   default folder:    ~/my-claude-backup
#   default repo name: the folder's name
set -euo pipefail

TOOLKIT_REPO="${TOOLKIT_REPO:-https://github.com/adityan-nd/claude-backup-toolkit.git}"
DIR="${1:-$HOME/my-claude-backup}"
NAME="${2:-$(basename "$DIR")}"

fail() { echo "ERROR: $*" >&2; exit 1; }

echo "==> Checking prerequisites"
for cmd in git python3 rsync gh; do
  command -v "$cmd" >/dev/null 2>&1 || fail "'$cmd' is not installed. Install it, then rerun."
done
gh auth status >/dev/null 2>&1 || fail "GitHub CLI is not logged in. Run: gh auth login   then rerun."
git config user.email >/dev/null 2>&1 || fail "git has no identity. Run:
  git config --global user.name \"Your Name\"
  git config --global user.email you@example.com
then rerun."
[ -d "$HOME/.claude" ] || fail "No ~/.claude folder. Use Claude Code at least once, then rerun."
[ -e "$DIR" ] && fail "$DIR already exists. Rerun with another folder:
  bash <(curl -fsSL https://raw.githubusercontent.com/adityan-nd/claude-backup-toolkit/main/install.sh) ~/another-folder"

echo "==> Creating your backup folder: $DIR"
git clone --quiet "$TOOLKIT_REPO" "$DIR"
cd "$DIR"
git remote remove origin  # your data must never be pushed to the public toolkit repo
chmod +x ./*.sh

echo "==> Copying your chats, skills and memory"
./backup_claude.sh

echo "==> Checking for secrets before anything is uploaded"
if ! python3 - "$DIR" <<'PY'
import os, re, sys
root = sys.argv[1]
pat = re.compile(r"AKIA[0-9A-Z]{16}|BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY|"
                 r"xox[baprs]-[0-9A-Za-z-]+|ghp_[0-9A-Za-z]{36}|AIza[0-9A-Za-z_-]{35}")
hits = []
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        p = os.path.join(dirpath, f)
        try:
            with open(p, errors="ignore") as fh:
                if pat.search(fh.read()):
                    hits.append(os.path.relpath(p, root))
        except OSError:
            pass
for h in hits:
    print("  possible secret in:", h)
sys.exit(1 if hits else 0)
PY
then
  cat <<EOF

Possible secrets found (listed above). NOTHING was uploaded.
Open those files and check. If a real key is there, delete it from the file
(and rotate that key). When it's clean, finish setup with:

  cd "$DIR" && gh repo create "$NAME" --private --source=. --remote=origin \\
    && git add -A && git commit -m "First backup" && git push -u origin main
EOF
  exit 1
fi

echo "==> Creating your private GitHub repo: $NAME"
gh repo create "$NAME" --private --source=. --remote=origin >/dev/null
git add -A
git commit --quiet -m "First backup"
git push --quiet -u origin main

cat <<EOF

Done. Your private backup repo: $(gh repo view --json url -q .url 2>/dev/null || echo "$NAME")
Local folder: $DIR

Back things up anytime:
  $DIR/backup_one_chat.sh <session-id>
  $DIR/backup_one_skill.sh <skill-name>
  $DIR/backup_memory.sh
  $DIR/backup_claude.sh   (everything; then git add/commit/push)
EOF
