# claude-backup-toolkit

Back up your Claude Code **chats, skills, and memory** to your own private
GitHub repo, and restore them anytime.

Claude Code keeps all of this as plain files in a hidden `~/.claude` folder on
your laptop, and nothing backs it up. Lose the laptop, reinstall, or switch
accounts, and it's gone. This toolkit copies it into a private repo you own.
It **never deletes** from the backup: if you clear a chat in Claude Code, the
backed-up copy stays.

---

## How it works (30-second version)

```
 THIS repo (public)                 YOUR repo (private)
 claude-backup-toolkit   ──clone──▶  ~/my-claude-backup  ──push──▶  github.com/<you>/my-claude-backup
 just the scripts                    scripts + your chats,
                                     skills, memory
```

You clone this repo **once**, turn the copy into your own private repo, and
from then on run one command whenever you want something backed up.

---

## Part 1 — One-time setup

### Before you start

Paste this. Every line should print a version or "Logged in". If one fails,
install that tool first.

```bash
bash --version | head -1
python3 --version
rsync --version | head -1
git --version
gh auth status          # if "not logged in": run  gh auth login
```

### Setup (copy-paste the whole block)

Replace `my-claude-backup` if you want a different name.

```bash
# 1. Get the scripts into a new folder of your own
git clone https://github.com/adityan-nd/claude-backup-toolkit.git ~/my-claude-backup
cd ~/my-claude-backup

# 2. Cut the link to this public repo, so your data can never be pushed here
git remote remove origin

# 3. Make the scripts runnable
chmod +x *.sh

# 4. Create YOUR private GitHub repo and connect this folder to it
gh repo create my-claude-backup --private --source=. --remote=origin

# 5. Copy everything in (chats, skills, memory) — this does NOT upload yet
./backup_claude.sh
```

You should see something like:

```
Rebuilt index: 42 sessions.
Backup refreshed at: /Users/alice/my-claude-backup
```

### Check, then upload

Chats contain whatever you ever pasted into Claude. If you might have pasted a
password or API key, run the scan in
[docs/03-scripts.md](docs/03-scripts.md#secret-hygiene) first. Then:

```bash
git add -A
git commit -m "First backup"
git push -u origin main
```

Open `https://github.com/<you>/my-claude-backup` and click `chats/INDEX.md`:
a table of every chat with its title and project. **Setup done.**

### Optional: nicer folder names

Your chats land in folders like `chats/-Users-alice-code-my-app` (Claude
Code's internal name for `/Users/alice/code/my-app`). To get `chats/my-app`
instead, see what folders you have:

```bash
ls ~/.claude/projects/
```

and add a line per project to `STATIC_MAP` in `names.py`:

```python
STATIC_MAP = {
    "-Users-alice-code-my-app": "my-app",
}
```

Already-backed-up folders need a one-time rename; see
[docs/04-naming.md](docs/04-naming.md). If some of your repos have their own
`.claude/` folder (project rules, project skills), add their paths to the
`REPOS` list in `backup_claude.sh` too.

---

## Part 2 — Backing things up, anytime

All commands run from your backup folder:

```bash
cd ~/my-claude-backup
```

| I want to... | Run | Uploads by itself? |
|---|---|---|
| Back up **one chat** | `./backup_one_chat.sh <session-id>` | Yes |
| Back up **one skill** | `./backup_one_skill.sh <skill-name>` | Yes |
| Back up **all memory** | `./backup_memory.sh` | Yes |
| Back up **one memory file** | `./backup_one_memory.sh <file-name>` | Yes |
| Back up **everything** | `./backup_claude.sh` then `git add -A && git commit -m "backup" && git push` | No, you push |

**Updating** something you already backed up is the same command again. It
re-copies the latest version and only uploads if something changed.

### Example: back up one chat

Each chat has a **session id**. Find it by the chat's title (the name shown in
Claude Code's sidebar):

```bash
grep -l '"customTitle":"Fix login bug"' ~/.claude/projects/*/*.jsonl
```

```
/Users/alice/.claude/projects/-Users-alice-code-my-app/352e1295-2261-402d-a7f3-577bb6c9059d.jsonl
```

The file name (without `.jsonl`) is the session id:

```bash
./backup_one_chat.sh 352e1295-2261-402d-a7f3-577bb6c9059d
```

```
Pushed: Fix login bug (352e1295-2261-402d-a7f3-577bb6c9059d)
```

Chat has no title? List the newest chats instead:
`ls -t ~/.claude/projects/*/*.jsonl | head -5`

### Example: back up one skill

See your skills, then pick one by its folder name:

```bash
ls ~/.claude/skills/
```

```
code-review-checklist   release-notes
```

```bash
./backup_one_skill.sh code-review-checklist
```

```
Pushed skill: code-review-checklist
```

### Example: back up memory

Just everything, no arguments:

```bash
./backup_memory.sh
```

```
Pushed full memory refresh.
```

Or one file (`ls ~/.claude/memory/` to see names):

```bash
./backup_one_memory.sh user-profile.md
```

### Example: you edited a skill and want the new version saved

Same command as before:

```bash
./backup_one_skill.sh code-review-checklist
```

```
Pushed skill: code-review-checklist          # if it changed
No changes for skill 'code-review-checklist' — already up to date.   # if not
```

---

## Part 3 — Getting it back

Deleted a chat, or on a new laptop? Clone your private repo and copy the files
back where Claude Code expects them:

```bash
git clone https://github.com/<you>/my-claude-backup.git ~/my-claude-backup
cd ~/my-claude-backup
rsync -a memory/ ~/.claude/memory/
rsync -a skills/ ~/.claude/skills/
```

Chats need one extra step (matching the project folder name); see
[docs/06-restore.md](docs/06-restore.md). To find a deleted chat by title,
look it up in `chats/INDEX.md`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `gh: command not found` / not logged in | Install GitHub CLI, then `gh auth login` |
| `Permission denied` running a script | `chmod +x *.sh` |
| `backup_one_*.sh` fails at `git push` | Folder has no remote yet: run step 4 of setup |
| `Session ... not found` | Use the id from the `.jsonl` file name (see example above), not the id in the Claude desktop app, which starts with `local_` and can differ |
| Ugly folder like `chats/-Users-alice-...` | Add it to `STATIC_MAP` in `names.py` ([docs/04-naming.md](docs/04-naming.md)) |
| `project-configs/` is empty | Normal unless you added repos to `REPOS` in `backup_claude.sh` |

---

## Docs

Full details on every script, naming, the chat index, and restoring:
[docs/README.md](docs/README.md).

## License

MIT — see [LICENSE](LICENSE).
