#!/usr/bin/env python3
"""Resolve Claude Code's internal project-path slug into a clean, readable folder name.

Works with zero setup: the name is taken from the project's real folder name,
read from the chat transcripts. STATIC_MAP is only for overriding a name you
don't like — see docs/04-naming.md.
"""
import json, os, re, sys

STATIC_MAP = {
    # "-Users-you-Documents-SourceCode-my-repo": "my-repo",
}

SCRATCH_RE = re.compile(r"(scratch-\d{4}-\d{2}-\d{2}-[0-9a-f]+)$")
PROJECTS = os.path.expanduser("~/.claude/projects")

def _slugify(path: str) -> str:
    # How Claude Code names project folders: every char except A-Z a-z 0-9 - becomes "-"
    return re.sub(r"[^A-Za-z0-9-]", "-", path)

def _from_cwd(slug: str):
    # ponytail: scans transcripts until a matching cwd is found; add a cache if
    # backups ever get slow on very large chat histories.
    try:
        files = os.listdir(os.path.join(PROJECTS, slug))
    except OSError:
        return None
    for fname in files:
        if not fname.endswith(".jsonl"):
            continue
        try:
            with open(os.path.join(PROJECTS, slug, fname), errors="ignore") as f:
                for line in f:
                    if '"cwd"' not in line:
                        continue
                    try:
                        cwd = json.loads(line).get("cwd")
                    except ValueError:
                        continue
                    if cwd and _slugify(cwd) == slug:
                        name = re.sub(r"[^A-Za-z0-9._-]", "-", os.path.basename(cwd))
                        return name or None
        except OSError:
            continue
    return None

def resolve(slug: str) -> str:
    if slug in STATIC_MAP:
        return STATIC_MAP[slug]
    m = SCRATCH_RE.search(slug)
    if m:
        return m.group(1)
    # Two different repos with the same folder name (e.g. ~/a/app and ~/b/app)
    # share one chats/app folder. Nothing is overwritten (chat files are named
    # by unique session id), and chats/INDEX.md still shows each chat's full path.
    return _from_cwd(slug) or slug

if __name__ == "__main__":
    print(resolve(sys.argv[1]))
