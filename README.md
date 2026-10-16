# claude-backup-toolkit

Repo-wise backup system for Claude Code's local state: chat transcripts,
skills, memory, and per-repo `.claude` project configs — plain file copies
kept in git, pushed to GitHub. No proprietary export format, nothing beyond
`rsync`/`cp` + `git` + `python3` stdlib.

Every script here only **adds or updates** — none of them delete. Clearing a
chat session, archiving a skill, or removing a memory file locally never
removes its backup copy.

## Quick start

```bash
chmod +x *.sh
git init && git branch -m main
echo -e ".DS_Store\n__pycache__/" > .gitignore
git add -A && git commit -m "Initial backup"
gh repo create <your-repo-name> --private --source=. --remote=origin --push
```

Edit `names.py`'s `STATIC_MAP` with your own repo slugs (see
[docs/04-naming.md](docs/04-naming.md)), and the `REPOS` array near the top of
`backup_claude.sh` with your own repo paths, then:

```bash
./backup_claude.sh        # full refresh
git add -A && git commit -m "backup" && git push
```

Or back up one thing at a time (each commits + pushes itself):

```bash
./backup_one_chat.sh <session_id>
./backup_one_skill.sh <skill-name>
./backup_one_memory.sh <filename>
./backup_memory.sh        # all memory files, no args
```

## Docs

Start at [docs/README.md](docs/README.md) for the full walkthrough: overview,
setup, every script explained, the naming system, the session index, and
restore steps.

## License

MIT — see [LICENSE](LICENSE).
