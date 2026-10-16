# claude-backup-toolkit

## What is this, and why would I want it?

Claude Code keeps everything you've built up with it — your past chats, your
custom skills, the things it has learned about you — as plain files in a hidden
`~/.claude` folder on your laptop. Nothing backs that folder up. If your
laptop dies, you reinstall, or you move to a new account, it's all gone.

This toolkit copies those files into a **private GitHub repo you own**,
organized by project, so you can browse old chats, restore anything you lose,
and carry your setup to a new machine. It never deletes anything from the
backup: if you clear a chat in Claude Code, the backed-up copy stays.

## What gets backed up

| What | Where it lives on your laptop | What that means in practice |
|---|---|---|
| **Chats** | `~/.claude/projects/` | The full transcript of every Claude Code session, grouped by the project folder you ran it in. |
| **Skills** | `~/.claude/skills/` | Your custom reusable instruction packs (each a folder with a `SKILL.md`). |
| **Memory** | `~/.claude/memory/` | Notes Claude keeps about you and your preferences across sessions. |
| **Project configs** | `<your-repo>/.claude/` | Per-project rules, handoff notes, and project-only skills inside each of your repos. `settings.local.json` is skipped on purpose — it can hold local permissions or tokens. |

## Prerequisites

Run each check command. If one fails, install that tool first.

- [ ] **bash** — `bash --version`
- [ ] **python3** (no extra packages needed) — `python3 --version`
- [ ] **rsync** — `rsync --version`
- [ ] **git** — `git --version`
- [ ] **GitHub CLI, logged in** — `gh auth status` (should say "Logged in to github.com"; if not, run `gh auth login`)

## Install (first time, about 5 minutes)

> **Two repos, don't mix them up.** *This* repo (`claude-backup-toolkit`) is
> just the scripts — public, shared. Your **backup repo** is a separate,
> **private** repo that you create below; it's where your actual chats and
> memory go. Never push your backup data to a public repo.

**1. Clone the toolkit into a new folder that will become your backup repo.**

```bash
git clone https://github.com/adityan-nd/claude-backup-toolkit.git ~/my-claude-backup
cd ~/my-claude-backup
```

**2. Detach it from the toolkit repo**, so your data can never be pushed back here.

```bash
git remote remove origin
```

**3. Make the scripts executable.**

```bash
chmod +x *.sh
```

**4. Tell `names.py` what your projects are called.**

Claude Code stores each project's chats in a folder named after the project's
full path, with `/`, `.` and spaces turned into `-`. So
`/Users/alice/code/my-app` becomes `-Users-alice-code-my-app`. That's ugly on
GitHub, so `names.py` maps it to a clean name.

See your own folder names:

```bash
ls ~/.claude/projects/
```

Then open `names.py` and add one line per project to `STATIC_MAP`:

```python
STATIC_MAP = {
    "-Users-alice-code-my-app": "my-app",
    "-Users-alice-work-billing-api": "billing-api",
}
```

Skipping this is fine: anything not listed is still backed up, just under its
ugly folder name. You can fix it later (see
[docs/04-naming.md](docs/04-naming.md)).

**5. Optional: list repos that have their own `.claude/` folder.**

If any of your repos contain a `.claude/` folder (project rules, project
skills), open `backup_claude.sh` and add their full paths to the `REPOS` array:

```bash
REPOS=(
  "/Users/alice/code/my-app"
  "/Users/alice/work/billing-api"
)
```

Leave it empty if you don't use per-project `.claude/` folders. Chats, skills,
and memory are backed up either way.

**6. Create your own private GitHub repo for the backup.**

```bash
gh repo create my-claude-backup --private --source=. --remote=origin
```

**7. Run the first backup.**

```bash
./backup_claude.sh
```

This copies everything into `chats/`, `skills/`, `memory/`, and
`project-configs/`, and builds `chats/INDEX.md` (a table of every chat by
title). **It does not commit or push** — that's on purpose, so you can look
first.

**8. Check for secrets, then commit and push.**

Skim `git status`. Chat transcripts contain whatever you pasted into Claude,
so if you ever pasted a password or API key, it's in there. See the secret
scan in [docs/03-scripts.md](docs/03-scripts.md#secret-hygiene). Then:

```bash
git add -A
git commit -m "First backup"
git push -u origin main
```

Done. Open your repo on GitHub and look at `chats/INDEX.md`.

## Day-to-day usage

Run these from inside your backup folder (`cd ~/my-claude-backup`).

**Back up everything** (new chats, skills, memory). Doesn't push; you commit:

```bash
./backup_claude.sh
git add -A && git commit -m "Weekly backup" && git push
```

**Back up one chat** (commits and pushes by itself). Find the session id in
`chats/INDEX.md`, or list newest transcripts for a project:

```bash
ls -t ~/.claude/projects/-Users-alice-code-my-app/*.jsonl | head -3
./backup_one_chat.sh 352e1295-2261-402d-a7f3-577bb6c9059d
```

Running it again on the same id updates that chat. It only commits if
something changed.

**Back up one skill** (folder name under `~/.claude/skills/`; commits and pushes):

```bash
./backup_one_skill.sh code-review-checklist
```

**Back up all memory** (no arguments; commits and pushes):

```bash
./backup_memory.sh
```

**Back up one memory file** (commits and pushes):

```bash
./backup_one_memory.sh user-profile.md
```

To restore onto a new laptop, see [docs/06-restore.md](docs/06-restore.md).

## Troubleshooting

**`gh: command not found` or "not logged in"**
Install the GitHub CLI, then run `gh auth login` and pick GitHub.com + HTTPS.

**`Permission denied` when running `./backup_claude.sh`**
The scripts aren't executable yet: `chmod +x *.sh`.

**`backup_one_*.sh` fails at `git push`**
Your backup folder has no remote yet. Do step 6 above.

**Nothing under `project-configs/`**
The `REPOS` array in `backup_claude.sh` is empty, or none of those repos has a
`.claude/` folder. Expected if you skipped step 5.

**A folder like `chats/-Users-alice-code-my-app` showed up**
That project isn't in `STATIC_MAP` yet. Add it to `names.py` and follow
[docs/04-naming.md](docs/04-naming.md) to rename the existing folder.

**`backup_one_chat.sh` says "Session ... not found"**
Use the file id, not the id shown in the Claude desktop app. The app's id
starts with `local_` and can differ from the transcript's file name. Use an id
from `chats/INDEX.md` or from `ls ~/.claude/projects/<project>/`.

## Docs

Start at [docs/README.md](docs/README.md) for the full walkthrough: overview,
setup, every script explained, the naming system, the session index, and
restore steps.

## License

MIT — see [LICENSE](LICENSE).
