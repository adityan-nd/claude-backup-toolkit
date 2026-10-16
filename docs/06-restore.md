# Restoring onto a new machine or account

There is no "import" tool — Claude Code reads its state straight off disk
under `~/.claude/`, so restoring is just copying files back to where they
came from.

## 1. Clone the backup repo

```bash
git clone https://github.com/<you>/<backup-repo>.git
cd <backup-repo>
```

## 2. Restore memory (global, applies to every project)

```bash
rsync -a memory/ "$HOME/.claude/memory/"
```

## 3. Restore skills (global)

```bash
rsync -a skills/ "$HOME/.claude/skills/"
```

## 4. Restore chats

Chats are keyed by clean repo name here, but Claude Code expects its own
internal path-slug directory under `~/.claude/projects/`. Two cases:

- **You're restoring into the same repo path as before** — find what slug
  Claude Code would use (open that project once, even a throwaway session,
  and `ls ~/.claude/projects/` to see the new slug appear), then:
  ```bash
  rsync -a "chats/<clean-name>/" "$HOME/.claude/projects/<that-slug>/"
  ```
- **You just want one session back** (e.g. to read it, or feed it to a fresh
  chat as context) — you don't need to restore it into `~/.claude/projects/`
  at all. Just open the `.jsonl` directly, or point a new Claude Code session
  at it and ask it to read the transcript as background context. There is no
  tool that "resumes" an old session id under a different account — a restored
  transcript is reference material, not a live resumable session.

## 5. Restore project-scoped configs

```bash
rsync -a "project-configs/<repo-name>/.claude/" "/path/to/<repo-name>/.claude/"
```

`settings.local.json` was deliberately excluded from the backup (it can hold
local permission grants/tokens) — recreate it fresh in the new environment
rather than restoring it.

## 6. Verify

- `ls ~/.claude/memory/` and `ls ~/.claude/skills/` should match the repo.
- Open Claude Code in a restored project and confirm `.claude/` content
  (rules, handoffs, project skills) is present.
- Use `chats/INDEX.md` to confirm which sessions exist and where they came
  from before you go looking for a specific one.
