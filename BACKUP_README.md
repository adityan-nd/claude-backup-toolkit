# My Claude Code backup

Private backup of my Claude Code **chats, skills, and memory**, made with
[claude-backup-toolkit](https://github.com/adityan-nd/claude-backup-toolkit).

The scripts here only add or update; they never delete. If a chat is cleared
or a skill removed in Claude Code, its copy here stays.

> **Keep this repo private.** It holds everything ever typed into Claude.
> To share the tool with someone, send them the public toolkit link instead.

## What's in here

| Folder | What it holds |
|---|---|
| [`chats/`](chats/) | Every chat transcript, one folder per project. **Start at [`chats/INDEX.md`](chats/INDEX.md)**: every chat by title, project, and session id. |
| [`skills/`](skills/) | Custom skills from `~/.claude/skills/` |
| [`memory/`](memory/) | Memory notes from `~/.claude/memory/` |
| [`project-configs/`](project-configs/) | `.claude/` folders from the repos listed in `REPOS` in `backup_claude.sh` |
| [`docs/`](docs/) | How the whole system works |

## Back up now

Run in any terminal, from any folder. Claude Code doesn't need to be open.

| To back up | Run |
|---|---|
| One chat | `"__BACKUP_DIR__/backup_one_chat.sh" <session-id>` |
| One skill | `"__BACKUP_DIR__/backup_one_skill.sh" <skill-name>` |
| All memory | `"__BACKUP_DIR__/backup_memory.sh"` |
| One memory file | `"__BACKUP_DIR__/backup_one_memory.sh" <file-name>` |
| Everything | `"__BACKUP_DIR__/backup_claude.sh"`, then push (below) |

The first four upload by themselves. **Everything** only copies, so push after it:

```bash
cd "__BACKUP_DIR__" && git add -A && git commit -m "Backup" && git push
```

Running a command again on the same chat, skill, or file **updates** it. It
only uploads if something changed.

### Finding the name or id to pass

- **Chat:** search by its title in the Claude Code sidebar. The file name,
  without `.jsonl`, is the session id:
  ```bash
  grep -l '"customTitle":"Fix login bug"' ~/.claude/projects/*/*.jsonl
  ```
  No title? Newest chats: `ls -t ~/.claude/projects/*/*.jsonl | head -5`
- **Skill:** `ls ~/.claude/skills/`
- **Memory file:** `ls ~/.claude/memory/`

### Or ask Claude

In any Claude Code chat, paste:

```
Back up this chat: find this session's transcript (the newest .jsonl in
~/.claude/projects/ for this project folder) and run
"__BACKUP_DIR__/backup_one_chat.sh" with its id.
```

```
Run "__BACKUP_DIR__/backup_memory.sh"
```

## Restore

On a new laptop, clone this repo, then copy files back to where Claude Code
reads them:

```bash
rsync -a memory/ ~/.claude/memory/
rsync -a skills/ ~/.claude/skills/
```

Chats need one extra step; see [docs/06-restore.md](docs/06-restore.md). To
find a chat you deleted, look it up by title in [`chats/INDEX.md`](chats/INDEX.md).
