#!/usr/bin/env python3
"""Back up and restore a repo's personal layer: the files you keep out of git.

Every repo has files that live only on your laptop because you told git to
ignore them in `.git/info/exclude`: prompt files, design drafts, a personal
`.claude/skills/`, local docker setups. Untracked files inside a nested
`.claude/` folder belong here too. None of it is in the team's remote, so a
lost laptop loses it. git can list exactly that set, so nothing is guessed.

Skipped on purpose: generated or heavy folders (graphify-out, node_modules,
target, dist, build, .venv), Claude Code's own state (worktrees, checkpoints,
mailbox, locks), anything that usually holds secrets (.env*, *.pem, *.key,
id_rsa*, settings.local.json), files over 50 MB, and the repo's root `.claude/`
(backup_claude.sh already copies that whole folder).

Usage:
  personal.py backup  <repo> <dest>            # copy the layer into <dest>, same paths
  personal.py restore <dest> <repo> [--force]  # copy it back; never overwrites without --force
  personal.py list    <repo>                   # print what backup would copy
  personal.py --self-test

Neither direction deletes anything.
"""
import filecmp, os, re, shutil, subprocess, sys, tempfile

MAX_BYTES = 50 * 1024 * 1024
SKIP = re.compile(
    r"(^|/)(graphify-out|node_modules|target|dist|build|\.venv|__pycache__)/"
    r"|(^|/)\.claude/(worktrees|checkpoints|mailbox|routines/\.state|agent-memory-local)(/|$)"
    r"|(^|/)(scheduled_tasks\.(lock|json)|agent-registry\.json|assistant-daemon-state\.json|first-run)$"
    r"|(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|settings\.local\.json|\.DS_Store)$"
    r"|^\.claude/"
)


def _git(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout
    return [p for p in out.decode().split("\0") if p]


def layer(repo):
    """Relative paths of the personal layer, and the ones skipped as too big."""
    exclude = subprocess.run(["git", "-C", repo, "rev-parse", "--git-path", "info/exclude"],
                             check=True, capture_output=True, text=True).stdout.strip()
    exclude = os.path.join(repo, exclude) if not os.path.isabs(exclude) else exclude
    paths = set()
    if os.path.isfile(exclude):
        paths.update(_git(repo, "ls-files", "-z", "--others", "--ignored", f"--exclude-from={exclude}"))
    paths.update(_git(repo, "ls-files", "-z", "--others", "--exclude-standard", "--", ":(glob)**/.claude/**"))
    keep, too_big = [], []
    for rel in sorted(paths):
        full = os.path.join(repo, rel)
        if SKIP.search(rel) or not os.path.isfile(full) or os.path.islink(full):
            continue
        (too_big if os.path.getsize(full) > MAX_BYTES else keep).append(rel)
    return keep, too_big


def _copy_new_or_changed(src, dst):
    if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


def backup(repo, dest):
    keep, too_big = layer(repo)
    copied = sum(_copy_new_or_changed(os.path.join(repo, rel), os.path.join(dest, rel)) for rel in keep)
    for rel in too_big:
        print(f"  WARN skipped (over 50 MB): {rel}")
    return len(keep), copied


def restore(dest, repo, force=False):
    restored, kept = 0, []
    for root, _, files in os.walk(dest):
        for name in files:
            src = os.path.join(root, name)
            rel = os.path.relpath(src, dest)
            dst = os.path.join(repo, rel)
            if os.path.exists(dst) and not force:
                if not filecmp.cmp(src, dst, shallow=False):
                    kept.append(rel)
                continue
            restored += _copy_new_or_changed(src, dst)
    for rel in kept:
        print(f"  kept your current copy (differs from backup; --force to replace): {rel}")
    return restored, kept


def _self_test():
    tmp = tempfile.mkdtemp()
    try:
        repo = os.path.join(tmp, "repo")
        files = {
            "tracked.md": "team file",
            "notes/MASTER-PROMPT.md": "mine",
            "dev/docker-compose.yml": "mine",
            "graphify-out/graph.json": "generated",
            ".env": "SECRET=1",
            "sub/.claude/rules.md": "nested claude file, untracked",
            ".claude/skills/s/SKILL.md": "root .claude, copied elsewhere",
            "draft.txt": "untracked but not excluded",
        }
        for rel, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(repo, rel)) or repo, exist_ok=True)
            with open(os.path.join(repo, rel), "w") as f:
                f.write(text)
        subprocess.run(["git", "init", "-q", repo], check=True)
        subprocess.run(["git", "-C", repo, "add", "tracked.md"], check=True)
        with open(os.path.join(repo, ".git", "info", "exclude"), "a") as f:
            f.write("notes/\ndev/\ngraphify-out/\n.env\n.claude/skills/\n")

        keep, _ = layer(repo)
        assert keep == ["dev/docker-compose.yml", "notes/MASTER-PROMPT.md", "sub/.claude/rules.md"], keep

        dest = os.path.join(tmp, "backup")
        assert backup(repo, dest) == (3, 3)
        assert backup(repo, dest) == (3, 0), "unchanged files were copied again"

        fresh = os.path.join(tmp, "fresh")
        os.makedirs(os.path.join(fresh, "notes"))
        with open(os.path.join(fresh, "notes", "MASTER-PROMPT.md"), "w") as f:
            f.write("newer local edit")
        restored, kept = restore(dest, fresh)
        assert (restored, kept) == (2, ["notes/MASTER-PROMPT.md"]), (restored, kept)
        assert open(os.path.join(fresh, "notes", "MASTER-PROMPT.md")).read() == "newer local edit"
        assert restore(dest, fresh, force=True)[0] == 1
        assert open(os.path.join(fresh, "notes", "MASTER-PROMPT.md")).read() == "mine"
        print("self-test passed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--self-test"]:
        _self_test()
    elif len(args) == 3 and args[0] == "backup":
        total, copied = backup(args[1], args[2])
        print(f"personal layer: {total} files, {copied} new or changed")
    elif len(args) in (3, 4) and args[0] == "restore" and args[3:] in ([], ["--force"]):
        restored, kept = restore(args[1], args[2], force=args[3:] == ["--force"])
        print(f"restored {restored} files, kept {len(kept)} newer local copies")
    elif len(args) == 2 and args[0] == "list":
        keep, too_big = layer(args[1])
        print("\n".join(keep))
        for rel in too_big:
            print(f"(skipped, over 50 MB) {rel}", file=sys.stderr)
    else:
        print(__doc__)
        sys.exit(2)
