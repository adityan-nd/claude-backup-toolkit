# Indexing — `index.py`

## Why

Session ids are UUIDs. Once a chat is buried in `chats/<repo>/`, you have no
way to find "that chat about the auth bug from last month" without opening
files one by one. The index solves that: a single table of
`session_id -> title -> repo/folder -> last backed up`.

It's also your safety net for the "never delete" rule: if you delete a
session locally, its row stays in the index forever (as long as its files are
still in `chats/`), so you can always look it up later.

## Files it produces

- `chats/INDEX.tsv` — machine-readable, tab-separated:
  `session_id  title  project_slug  cwd  last_backed_up`
- `chats/INDEX.md` — the same data as a readable markdown table, meant to be
  browsed directly on GitHub.

## Two modes

```bash
index.py upsert <dest> <session_id> <title> <slug> <cwd>
```
Updates (or inserts) exactly one row. Used internally by `backup_one_chat.sh`
after it copies a session — cheap, doesn't touch any other row.

```bash
index.py rebuild <dest>
```
Full rescan: walks every `chats/<repo>/*.jsonl`, re-derives title (from that
session's `custom-title.json`, falling back to the session id) and `cwd`
(parsed out of the transcript's first line that has one), and regenerates
both files from scratch. Used by `backup_claude.sh`. Existing
`last_backed_up` timestamps are preserved for rows that already existed —
only genuinely new rows get a fresh timestamp.

## Never-delete guarantee

`rebuild` derives its session list by scanning what's actually present in
`chats/` on disk — it never removes a row for a session whose files are still
there. Since the backup scripts never delete files either, a row only
disappears from the index if you manually delete that session's files from
the repo yourself.

## Using it to restore a deleted session

1. Open `chats/INDEX.md` on GitHub (or `grep` the `.tsv` locally).
2. Find the session by title, note its `session_id` and repo/folder column.
3. Its files are at `chats/<project_slug>/<session_id>.jsonl` (+ the sidecar
   folder of the same name, if one exists). See
   [06-restore.md](06-restore.md) for copying it back into place.
