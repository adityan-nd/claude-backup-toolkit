# Naming — `names.py`

## The problem it solves

Claude Code stores each project's chats under a directory named by mangling
the working-directory path: `/` becomes `-`, so
`/Users/alice/Documents/SourceCode/my-app` becomes the slug
`-Users-alice-Documents-SourceCode-my-app`. That's what you'd see as a folder
name on GitHub if you backed it up verbatim — unreadable, and because spaces
in real folder names (`My Side Project`) also turn into
hyphens, the slug is ambiguous to reverse mechanically.

`names.py` maps each slug to a clean, human name instead. **It works with no
setup**: you normally never edit it.

## How it works

`resolve(slug)` tries these in order and uses the first that works:

1. **`STATIC_MAP`** — your manual overrides. Empty by default.
2. **Scratch workspaces** — Claude Code desktop's throwaway "no folder" chats
   live under a long `.../scratch-workspaces/<guid>/<guid>/scratch-DATE-HASH`
   path. A regex takes the trailing `scratch-YYYY-MM-DD-hash` as the name.
3. **The real folder name** — every chat transcript records the folder it ran
   in (its `cwd`). `names.py` reads the transcripts in that project, finds a
   `cwd` that turns into exactly this slug (Claude Code's rule: every
   character except `A-Z a-z 0-9 -` becomes `-`), and uses that folder's name.
   `/Users/alice/code/My App` becomes `My-App`.
4. **The slug itself** — only if none of the above works (no chat in the
   project recorded its path). Rare.

Two different repos with the same folder name (`~/a/app` and `~/b/app`) share
one `chats/app` folder. Nothing is overwritten, since each chat file is named
by its unique session id, and `chats/INDEX.md` shows every chat's full path.
If you'd rather keep them apart, give one a `STATIC_MAP` entry.

## Overriding a name

1. Find its slug: `ls ~/.claude/projects/`.
2. Add a line to `STATIC_MAP` in `names.py`:
   ```python
   "-Users-alice-Documents-SourceCode-new-repo": "new-repo",
   ```
3. Re-run `backup_claude.sh`. New backups land under the new name
   immediately. Sessions already backed up under the old name need a one-time
   manual `git mv`:
   ```bash
   git mv "chats/-Users-alice-Documents-SourceCode-new-repo" "chats/new-repo"
   python3 index.py rebuild "$(pwd)"
   git add -A && git commit -m "Rename new-repo chats to clean name"
   ```

## Public vs private

GitHub repo visibility (public/private) is a **repo-level** setting — it
cannot differ by branch. You cannot have one branch of a repo be public and
another private. If you want to share the *tooling* (these scripts) with
teammates without exposing your actual chat/skill/memory content, the answer
is **two separate repos**: a private one with real content, and a public one
containing only the scripts (with `STATIC_MAP` left empty).
