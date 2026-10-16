# Naming — `names.py`

## The problem it solves

Claude Code stores each project's chats under a directory named by mangling
the working-directory path: `/` becomes `-`, so
`/Users/alice/Documents/SourceCode/nxt` becomes the slug
`-Users-alice-Documents-SourceCode-nxt`. That's what you'd see as a folder
name on GitHub if you backed it up verbatim — unreadable, and because spaces
in real folder names (`PM-5144 FleetMap Prod Validation`) also turn into
hyphens, the slug is ambiguous to reverse mechanically.

`names.py` maps each slug to a clean, human name instead.

## How it works

```python
STATIC_MAP = {
    "-Users-alice-Documents-SourceCode-nxt": "nxt",
    "-Users-alice-Desktop-Some-Project": "Some-Project",
    # ... one entry per repo you actually use
}

SCRATCH_RE = re.compile(r"(scratch-\d{4}-\d{2}-\d{2}-[0-9a-f]+)$")

def resolve(slug: str) -> str:
    if slug in STATIC_MAP:
        return STATIC_MAP[slug]
    m = SCRATCH_RE.search(slug)
    if m:
        return m.group(1)
    return slug  # unknown slug: keep as-is rather than guess wrong
```

- **Known repos** — a hardcoded dict, one entry per slug you've actually seen
  under `~/.claude/projects/`. This is the only part you edit.
- **Scratch workspaces** — Claude Code desktop's throwaway "no folder" chats
  live under a long `.../scratch-workspaces/<guid>/<guid>/scratch-DATE-HASH`
  path. The trailing `scratch-YYYY-MM-DD-hash` segment is a reliable,
  mechanically-extractable name, so a regex handles all of these without
  needing a dict entry each time.
- **Unknown slug** — if neither matches, `resolve()` returns the slug
  unchanged rather than guessing wrong. You'll see an ugly folder name appear
  in `chats/` the first time you use a new repo — that's your signal to add
  a `STATIC_MAP` entry for it.

## Adding a new repo

1. Find its slug: `ls ~/.claude/projects/` and look for the one matching your
   repo's path (or just run a backup once and see what ugly name shows up).
2. Add a line to `STATIC_MAP` in `names.py`:
   ```python
   "-Users-alice-Documents-SourceCode-new-repo": "new-repo",
   ```
3. Re-run `backup_claude.sh` — new sessions from that repo land under the
   clean name immediately. Existing already-backed-up sessions under the old
   ugly slug name need a one-time manual `git mv`:
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
containing only the scripts (with `STATIC_MAP` stripped to a generic example).
