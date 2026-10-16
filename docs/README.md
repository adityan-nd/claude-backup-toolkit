# Claude Full Backup — docs index

A repo-wise backup system for Claude Code's local state: chat transcripts,
skills, memory, and per-repo `.claude` project configs. Built so it can be
replicated in anyone's own repo from scratch.

Read in this order:

1. [01-overview.md](01-overview.md) — what this backs up and why, the "never delete" rule
2. [02-setup.md](02-setup.md) — prerequisites to run or replicate this system
3. [03-scripts.md](03-scripts.md) — every script, what it does, exact usage
4. [04-naming.md](04-naming.md) — how `names.py` turns ugly path-slugs into clean folder names
5. [05-indexing.md](05-indexing.md) — the session_id → title → repo lookup table
6. [06-restore.md](06-restore.md) — bringing chats/skills/memory back on a new machine/account
