# Scripts

## `backup_claude.sh` — full refresh

No arguments. Run anytime to resync everything:

```bash
./backup_claude.sh
```

What it does, in order:

1. **Chats** — for every directory under `~/.claude/projects/*/`, resolves
   its internal path-slug to a clean name via `names.py`, then
   `rsync -a`'s the whole project directory into `chats/<clean-name>/`.
2. **Skills** — `rsync -a` of `~/.claude/skills/` → `skills/`.
3. **Memory** — `rsync -a` of `~/.claude/memory/` → `memory/`.
4. **Project configs** — for each repo in the `REPOS` array (hardcoded list
   at the top of the script — add your own repos here), if it has a
   `.claude/` directory, copies it into `project-configs/<repo-name>/.claude/`,
   excluding `settings.local.json` (can hold local permission grants/tokens
   you don't want in git).
5. **Rebuilds the index** — calls `index.py rebuild` (see
   [05-indexing.md](05-indexing.md)).

It does **not** `git commit` or `git push` — that's left to you, since a full
refresh can touch hundreds of files and is worth a `git status` look before
committing.

## `backup_one_chat.sh` — one chat, own commit

```bash
./backup_one_chat.sh <session_id> [<session_id> ...]
```

For each session id: finds it under `~/.claude/projects/*/`, resolves the
clean folder name, copies the `.jsonl` (+ its sidecar folder if present),
extracts the session's title (from `custom-title.json`) and `cwd` (parsed out
of the transcript itself), upserts that into the index, then **commits and
pushes immediately** with message `Backup chat: <title> (<session_id>)`.

Rerunning it on an already-backed-up id is also the "update" command — it
re-copies and only commits if something actually changed
(`git diff --cached --quiet` check).

## `backup_one_skill.sh` / `backup_one_memory.sh` — same pattern

```bash
./backup_one_skill.sh <skill-name> [<skill-name> ...]
./backup_one_memory.sh <filename> [<filename> ...]
```

Same shape as `backup_one_chat.sh`: copy, commit, push, per item, skip if
nothing changed. `backup_one_skill.sh` copies the whole
`~/.claude/skills/<name>/` directory; `backup_one_memory.sh` copies one file
from `~/.claude/memory/`.

## `backup_memory.sh` — all memory, no arguments

```bash
./backup_memory.sh
```

Syncs the entire `~/.claude/memory/` directory in one shot and commits/pushes
if anything changed. Exists because memory files are small, numerous, and you
usually want "just back up all of it" rather than naming each file.

## Secret hygiene

Before the very first push (and anytime you add a new kind of file to the
backup), scan for obvious secret patterns. Recursive `grep -r` / `find`
whole-tree scans can be slow or blocked by some tool-call guards — a small
Python walk is reliable:

```python
import os, re
pat = re.compile(r"AKIA[0-9A-Z]{16}|BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY|"
                  r"xox[baprs]-[0-9A-Za-z-]+|ghp_[0-9A-Za-z]{36}|AIza[0-9A-Za-z_-]{35}")
for dirpath, _, files in os.walk("."):
    if ".git" in dirpath.split(os.sep):
        continue
    for f in files:
        p = os.path.join(dirpath, f)
        try:
            with open(p, errors="ignore") as fh:
                if pat.search(fh.read()):
                    print("FLAGGED:", p)
        except Exception:
            pass
```

Treat every hit as a real finding until you've opened the file and confirmed
it's a false positive (test fixture, placeholder, etc.) — don't skip the read.
