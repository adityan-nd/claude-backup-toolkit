# Overview

## The problem

Claude Code (the CLI/desktop app) keeps three kinds of local state that are
easy to lose and hard to move between machines or accounts:

- **Chats** — every session's full transcript, stored as JSONL under
  `~/.claude/projects/<path-slug>/<session-id>.jsonl`, grouped by the
  directory you ran the session in.
- **Skills** — reusable instruction bundles under `~/.claude/skills/<name>/`.
- **Memory** — the `user`/`feedback`/`project`/`reference` notes Claude
  accumulates across sessions, under `~/.claude/memory/`.

None of this is backed up anywhere by default. If the machine dies, the
`~/.claude` folder gets wiped, or you switch accounts, it's gone.

## The approach

This repo is a **plain copy of the real files**, organized repo-wise, kept in
git, pushed to GitHub. No proprietary export format, no API dependency beyond
what's already on disk — just `rsync`/`cp` + `git`.

Two ways to run it:

- **Full refresh** (`backup_claude.sh`) — syncs everything in one pass.
- **One-at-a-time** (`backup_one_chat.sh`, `backup_one_skill.sh`,
  `backup_one_memory.sh`) — back up and push a single chat/skill/memory file
  as its own commit, so you can be selective and keep history readable.

## The "never delete" rule

Every script in this repo only **adds or updates** files — none of them ever
pass `--delete` to `rsync`, call `rm`, or remove a row from the index.

This is deliberate: if you clear or delete a chat session locally, archive a
skill, or decide you don't need a memory file anymore, **that is a statement
about your local workspace, not about the backup.** The backup is a permanent
record. The only way anything disappears from this repo is if you manually
delete it from the repo yourself.

## Layout

```
.
├── chats/
│   ├── INDEX.md                 # human-readable session_id -> title -> repo map
│   ├── INDEX.tsv                # same, machine-readable
│   ├── <clean-repo-name>/
│   │   ├── <session-id>.jsonl
│   │   └── <session-id>/        # sidechains, tool-result blobs, custom-title.json
│   └── ...
├── skills/
│   └── <skill-name>/            # copy of ~/.claude/skills/<skill-name>/
├── memory/
│   └── *.md                     # copy of ~/.claude/memory/
├── project-configs/
│   └── <repo-name>/.claude/     # per-repo .claude dir (handoffs, rules, project skills)
│                                 # settings.local.json is excluded (can hold local tokens)
├── backup_claude.sh
├── backup_one_chat.sh
├── backup_one_skill.sh
├── backup_one_memory.sh
├── backup_memory.sh
├── names.py
├── index.py
└── docs/
```
