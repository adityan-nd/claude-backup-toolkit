#!/usr/bin/env python3
"""
Maintains chats/INDEX.tsv + chats/INDEX.md: session_id -> title -> repo/folder.
Never removes a row for a session whose files still exist in chats/ —
mirrors the backup scripts' "never delete" rule.

Usage:
  index.py upsert <dest> <session_id> <title> <slug> <cwd>   # one session (used by backup_one_chat.sh)
  index.py rebuild <dest>                                    # full rescan (used by backup_claude.sh)
"""
import sys, csv, os, json
from datetime import datetime, timezone

def load_rows(tsv_path):
    rows = {}
    if os.path.exists(tsv_path):
        with open(tsv_path, newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    rows[row[0]] = row
    return rows

def write_rows(dest, rows):
    tsv_path = os.path.join(dest, "chats", "INDEX.tsv")
    with open(tsv_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["session_id", "title", "project_slug", "cwd", "last_backed_up"])
        for sid in sorted(rows, key=lambda k: rows[k][1].lower()):
            writer.writerow(rows[sid])

    md_path = os.path.join(dest, "chats", "INDEX.md")
    with open(md_path, 'w') as f:
        f.write("# Chat Session Index\n\n")
        f.write("session_id -> title -> repo/folder it ran in. Use this to find or restore a chat "
                "you deleted locally — its files are still under chats/<project_slug>/<session_id>.jsonl.\n\n")
        f.write("| Title | Session ID | Repo / Folder | Last backed up |\n|---|---|---|---|\n")
        for sid in sorted(rows, key=lambda k: rows[k][1].lower()):
            _, title, slug, cwd, ts = rows[sid]
            folder = cwd if cwd else slug
            f.write(f"| {title} | `{sid}` | {folder} | {ts} |\n")

def extract_cwd(jsonl_path):
    try:
        with open(jsonl_path, errors='ignore') as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get('cwd'):
                    return d['cwd']
    except Exception:
        pass
    return ""

def extract_title(slug_dir, session_id):
    title_path = os.path.join(slug_dir, session_id, "custom-title.json")
    if os.path.exists(title_path):
        try:
            with open(title_path) as f:
                t = json.load(f).get("title")
                if t:
                    return t
        except Exception:
            pass
    return session_id

def cmd_upsert(dest, session_id, title, slug, cwd):
    rows = load_rows(os.path.join(dest, "chats", "INDEX.tsv"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows[session_id] = [session_id, title, slug, cwd, now]
    write_rows(dest, rows)

def cmd_rebuild(dest):
    chats_root = os.path.join(dest, "chats")
    existing = load_rows(os.path.join(chats_root, "INDEX.tsv"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = {}
    for slug in sorted(os.listdir(chats_root)):
        slug_dir = os.path.join(chats_root, slug)
        if not os.path.isdir(slug_dir):
            continue
        for fname in os.listdir(slug_dir):
            if not fname.endswith(".jsonl"):
                continue
            session_id = fname[:-len(".jsonl")]
            jsonl_path = os.path.join(slug_dir, fname)
            title = extract_title(slug_dir, session_id)
            cwd = extract_cwd(jsonl_path)
            prev = existing.get(session_id)
            ts = prev[4] if prev else now
            rows[session_id] = [session_id, title, slug, cwd, ts]
    write_rows(dest, rows)
    print(f"Rebuilt index: {len(rows)} sessions.")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "upsert":
        _, _, dest, session_id, title, slug, cwd = sys.argv
        cmd_upsert(dest, session_id, title, slug, cwd)
    elif mode == "rebuild":
        cmd_rebuild(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
