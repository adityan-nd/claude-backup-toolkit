# Setup / prerequisites

**Fastest path:** `install.sh` does everything on this page in one command
(see the main README). This page explains what it does, for doing it by hand.

To run this system (or replicate it in your own repo) you need:

- **bash** — the macOS built-in bash 3.2 is enough
- **python3** — used for JSON parsing (session titles, `cwd` extraction) and
  the index/naming logic. No third-party packages; stdlib only
  (`json`, `csv`, `os`, `re`, `datetime`, `sys`).
- **rsync** — does the actual file copying (`-a`, additive only)
- **git** — the backup destination is a git repo
- **GitHub CLI (`gh`)**, authenticated (`gh auth status`) — only needed once,
  to create the remote repo. After that, plain `git push` is enough.

## One-time setup (replicating this from scratch)

```bash
mkdir -p "$HOME/Desktop/Claude Full Backup"
cd "$HOME/Desktop/Claude Full Backup"
# ...copy in backup_claude.sh, backup_one_chat.sh, backup_one_skill.sh,
#    backup_one_memory.sh, backup_memory.sh, names.py, index.py...
chmod +x *.sh
git init
git branch -m main
cat > .gitignore << 'EOF'
.DS_Store
__pycache__/
EOF
```

Then create the GitHub repo (decide private vs public — see
[the public/private note](04-naming.md#public-vs-private) for why a single
repo can't be both):

```bash
gh repo create <repo-name> --private --source=. --remote=origin --push
```

## First run

```bash
./backup_claude.sh
```

This does a full sync of chats/skills/memory/project-configs and rebuilds the
chat index, but does **not** commit or push — review `git status` first
(especially for secrets — see the note in
[03-scripts.md](03-scripts.md#secret-hygiene)), then:

```bash
git add -A
git commit -m "Initial backup"
git push -u origin main
```

After that, `backup_claude.sh` leaves committing/pushing to you (it's a bulk
operation you'll want to review), while the `backup_one_*.sh` scripts commit
and push automatically per item, since each is a small, self-contained change.
