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

Before the very first push (and anytime you're unsure), scan the backup
folder. `install.sh` runs this automatically and refuses to upload if it
finds anything:

```bash
python3 scan_secrets.py .
```

It looks for AWS access key IDs, GitHub tokens, Slack tokens, Google API keys,
and private keys, and prints each file with a short masked preview. It
deliberately ignores things that look like secrets but aren't:

- an AWS key ID inside a pre-signed S3 link (`X-Amz-Credential=AKIA…`): the ID
  alone isn't a secret, and these links show up constantly in chats,
- obvious fakes from docs and tests: all zeros, repeated characters,
  `EXAMPLE`, alphabet runs like `0123456789ABCDEF`,
- a private-key header mentioned in text with no actual key after it.

`python3 scan_secrets.py --self-test` checks these rules still catch real-shaped
secrets and skip the fakes.

Treat every hit as real until you've opened the file and confirmed otherwise.
If it is real: rotate the key first, then remove it from the backup file
**and** from the original under `~/.claude/projects/`, or the next backup
copies it back.
