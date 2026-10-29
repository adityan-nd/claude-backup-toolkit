# Scripts

## `backup.sh` — everything, one command

```bash
./backup.sh                        # refresh, scan, commit, push
./backup.sh --no-push              # commit locally, review before pushing
./backup.sh --force                # re-extract every transcript (after upgrading)
./backup.sh --with-shell-history   # also copy ~/.zsh_history
```

Runs `backup_claude.sh` to do the copying, then scans for secrets, commits and
pushes. If `scan_secrets.py` finds anything, **nothing is committed** — fix it
and rerun. This is the command to use day to day; the scripts below are the
pieces it builds on, still useful on their own.

`--with-shell-history` is off by default on purpose: shell history routinely
contains tokens pasted into commands, and `scan_secrets.py`'s five patterns
will not catch most of them. Every command Claude ran is already in the
transcripts either way.

## `media.py` — attachments out of transcripts

Claude Code inlines every screenshot, PDF and attachment into the `.jsonl`
transcript as base64. On a browser- or simulator-heavy session that is most of
the file, and the same screenshot is re-sent on each turn it stays in context
— so one image can appear dozens of times. Transcripts reach hundreds of
megabytes and GitHub **rejects any file over 100 MiB**, which fails the push.

`media.py` stores each distinct blob once per session and leaves a reference:

```
chats/<project>/<session-id>.jsonl          text only
chats/<project>/<session-id>/media/<sha>.jpg
```

Files are named by the sha256 of their contents, so a repeated image is stored
once. The extension comes from the block's `media_type` — images, audio, PDF,
HTML, CSV all handled; anything unrecognised is kept as `.bin` rather than
dropped. Base64 that fails to decode is left inline with a warning, never
discarded.

Called automatically by `backup_claude.sh` and `backup_one_chat.sh`. Directly:

```bash
python3 media.py sync ~/.claude/projects ./chats     # all transcripts
python3 media.py extract <src.jsonl> <dst.jsonl> <media-dir>
python3 media.py restore <src.jsonl> <dst.jsonl> <media-dir>
python3 media.py --self-test
```

`restore` is the inverse: it reads the media files back and rebuilds a
transcript Claude Code can load, byte-identical to the original. Run it before
copying a transcript back into `~/.claude/projects/` — see
[06-restore.md](06-restore.md).

Only transcripts whose source is newer than their backup copy are re-read, so
a repeat run takes seconds. After upgrading the toolkit, use `--force` once so
transcripts copied by an older version get re-processed.

## `backup_claude.sh` — full refresh

No arguments. Run anytime to resync everything:

```bash
./backup_claude.sh
```

What it does, in order:

1. **Chats** — hands `~/.claude/projects/` to `media.py sync`, which resolves
   each internal path-slug to a clean name via `names.py`, copies every
   transcript into `chats/<clean-name>/`, and splits attachments out into
   `chats/<clean-name>/<session-id>/media/` (see above).
2. **Skills** — `rsync -a` of `~/.claude/skills/` → `skills/`.
3. **Memory** — `rsync -a` of `~/.claude/memory/` → `memory/`.
   Also copies `~/.claude/commands/` and `~/.claude/history.jsonl`
   (your typed prompts) → `prompt-history.jsonl`.
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
- a private-key header mentioned in text with no actual key after it,
- a match buried inside a much longer unbroken base64 run. Tool output is
  full of large base64 blobs, and a 12,000-character one contains `AIza`
  followed by 35 random characters purely by chance. A genuine key is its own
  token, so its run is its own length; a chance substring sits in the middle
  of something far longer. The randomness check cannot separate these — a
  random slice of base64 *is* random — so only the surroundings can.

`python3 scan_secrets.py --self-test` checks these rules still catch real-shaped
secrets and skip the fakes.

Treat every hit as real until you've opened the file and confirmed otherwise.
If it is real: rotate the key first, then remove it from the backup file
**and** from the original under `~/.claude/projects/`, or the next backup
copies it back.
