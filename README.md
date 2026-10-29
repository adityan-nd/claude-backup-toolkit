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
 claude-backup-toolkit   ──setup──▶  ~/my-claude-backup  ──push──▶  github.com/<you>/my-claude-backup
 just the scripts                    scripts + your chats,
                                     skills, memory
```

Setup runs **once**. After that, one command whenever you want something
backed up.

---

## Part 1 — One-time setup (one command)

### You need

`git`, `python3`, `rsync`, and the GitHub CLI logged in (`gh auth login`).
The installer checks all of these and tells you exactly what's missing.

### Option A: run it yourself

Paste into a terminal:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/adityan-nd/claude-backup-toolkit/main/install.sh)
```

That's the whole setup. It:

1. creates `~/my-claude-backup` from this toolkit and disconnects it from this
   public repo, so your data can never be pushed here,
2. copies in your chats, skills, and memory (folders get readable names like
   `chats/my-app` automatically),
3. scans for leaked passwords/API keys and **stops without uploading** if it
   finds any,
4. creates a **private** GitHub repo `my-claude-backup` under your account and
   pushes the first backup.

Want a different folder or repo name? Add them at the end:
`bash <(curl ...install.sh) ~/backups/claude claude-backup-2026`

### Option B: let Claude do it

Open any Claude Code chat (any model works, even the smallest, since it only
runs one command) and paste:

```
Set up my Claude backup. Run this one command and tell me the result:
bash <(curl -fsSL https://raw.githubusercontent.com/adityan-nd/claude-backup-toolkit/main/install.sh)
If it reports a missing tool or a possible secret, explain in plain words
what I need to do and stop. Don't work around it.
```

Claude will ask you to approve the command (or runs it directly if you've
turned on bypass permissions).

### When it's done

You'll see:

```
Done. Your private backup repo: https://github.com/<you>/my-claude-backup
Local folder: /Users/<you>/my-claude-backup
```

Open that link. Its front page is a README written for **your** backup: what's
in it, and every backup command ready to copy with your folder path filled in.
`chats/INDEX.md` lists every chat with its title and project.

**If it stopped on "possible secret":** nothing was uploaded. Open the listed
file, remove the key (and rotate it, since it was exposed), then run the
finish command the installer printed.

### Optional: repos with their own `.claude/` folder

If some of your repos keep project rules or skills in a `.claude/` folder,
add their paths to the `REPOS` list near the top of
`~/my-claude-backup/backup_claude.sh`:

```bash
REPOS=(
  "/Users/alice/code/my-app"
)
```

<details>
<summary>Manual setup (what the installer does, step by step)</summary>

```bash
git clone https://github.com/adityan-nd/claude-backup-toolkit.git ~/my-claude-backup
cd ~/my-claude-backup
git remote remove origin            # never push your data to the public toolkit
chmod +x *.sh
./backup_claude.sh                  # copies everything in; does NOT upload
python3 scan_secrets.py .           # must print nothing before you upload
gh repo create my-claude-backup --private --source=. --remote=origin
git add -A && git commit -m "First backup" && git push -u origin main
```

</details>

---

## Part 2 — Backing things up, anytime

### Where and when do I run these?

- **Where:** in a normal terminal (Terminal app, iTerm, VS Code terminal). Not
  inside a Claude chat box. You don't need Claude Code open at all.
- **When:** anytime. Mid-chat, after a chat, days later. Backing up a chat that
  is still open just saves everything up to that moment; run it again later to
  save the rest.
- **Which chat:** any chat, by its session id. You don't have to open that chat
  first. One terminal can back up all your chats, skills, and memory.
- **From any folder:** use the full path, e.g.
  `~/my-claude-backup/backup_memory.sh`. It always saves into your backup
  folder, wherever you run it from.

**Prefer not to use a terminal?** In any Claude Code chat, just ask Claude to
run it. For example, paste one of these:

```
Run ~/my-claude-backup/backup_memory.sh
```

```
Back up this chat: find this session's transcript (the newest .jsonl in
~/.claude/projects/ for this project folder) and run
~/my-claude-backup/backup_one_chat.sh with its id.
```

```
Run ~/my-claude-backup/backup_one_skill.sh code-review-checklist
```

The examples below assume you're in the backup folder:

```bash
cd ~/my-claude-backup
```

| I want to... | Run | Uploads by itself? |
|---|---|---|
| Back up **everything** | `./backup.sh` | Yes |
| Back up **one chat** | `./backup_one_chat.sh <session-id>` | Yes |
| Back up **one skill** | `./backup_one_skill.sh <skill-name>` | Yes |
| Back up **all memory** | `./backup_memory.sh` | Yes |
| Back up **one memory file** | `./backup_one_memory.sh <file-name>` | Yes |
| Copy everything in, **without** committing | `./backup_claude.sh` | No |

Most of the time it's just:

```bash
./backup.sh
```

That refreshes everything, checks it for secrets, commits and pushes. If it
finds a possible secret it stops and commits nothing. Only transcripts that
actually changed are re-read, so a routine run takes seconds. Add `--no-push`
to commit locally and look before uploading.

**Updating** something you already backed up is the same command again. It
re-copies the latest version and only uploads if something changed.

### Screenshots and attachments

Claude Code inlines every screenshot, PDF and attachment into the chat
transcript as base64, and re-sends the same image on each turn it stays in
context. Transcripts get big — hundreds of megabytes for a browser- or
simulator-heavy session — and **GitHub refuses any file over 100 MiB**, so the
push fails.

The toolkit handles this for you: attachments are stored once per session
under `chats/<project>/<session-id>/media/`, and the transcript keeps a
reference. Nothing is lost — `python3 media.py restore` rebuilds the original
transcript byte-for-byte before you copy it back. You don't need to run
anything extra; `backup.sh` and `backup_one_chat.sh` already do it.

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
| `git has no identity` | `git config --global user.name "Your Name"` and `git config --global user.email you@example.com` |
| `... already exists` from the installer | You already set up. Use the backup commands in Part 2, or pass a new folder name |
| `Permission denied` running a script | `chmod +x ~/my-claude-backup/*.sh` |
| `backup_one_*.sh` fails at `git push` | Folder isn't connected to GitHub yet: run the finish command the installer printed |
| `Session ... not found` | Use the id from the `.jsonl` file name (see example above), not the id in the Claude desktop app, which starts with `local_` and can differ |
| A chat folder has an ugly name like `chats/-Users-alice-...` | None of its chats recorded the project's real path, so no name could be worked out. Pick one in `STATIC_MAP` in `names.py` ([docs/04-naming.md](docs/04-naming.md)) |
| `project-configs/` is empty | Normal unless you added repos to `REPOS` in `backup_claude.sh` |

---

## Docs

Full details on every script, naming, the chat index, and restoring:
[docs/README.md](docs/README.md).

## License

MIT — see [LICENSE](LICENSE).
