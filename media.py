#!/usr/bin/env python3
"""Pull media (images, audio, documents) out of chat transcripts into files.

Claude Code inlines every screenshot, PDF and attachment into the .jsonl
transcript as base64. That is ~45% of all transcript bytes here, and three
quarters of it is the same blob re-sent on later turns. Left inline it pushes
single transcripts past GitHub's 100 MiB hard limit.

This stores each distinct blob once per session, under the session's own
folder, and leaves a reference in its place:

  chats/<project>/<session-id>.jsonl          text only
  chats/<project>/<session-id>/media/<sha>.jpg

The reference keeps every original field, so `restore` rebuilds a transcript
Claude Code can load again. Media type decides the extension; anything
unrecognised is kept as .bin rather than dropped.

Usage:
  media.py sync <projects-root> <dest-chats-dir>   # back up every transcript
  media.py extract <src.jsonl> <dst.jsonl> <media-dir>
  media.py restore <src.jsonl> <dst.jsonl> <media-dir>
  media.py --self-test
"""
import base64, binascii, hashlib, json, os, sys

REF_TYPE = "claude-backup-ref"

# Only formats actually seen in transcripts get a real extension; the rest
# fall back to .bin so nothing is silently lost.
EXT = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "image/gif": ".gif", "image/svg+xml": ".svg",
    "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/webm": ".weba",
    "audio/mp4": ".m4a", "audio/ogg": ".ogg",
    "video/mp4": ".mp4", "video/webm": ".webm",
    "application/pdf": ".pdf", "application/json": ".json",
    "text/html": ".html", "text/markdown": ".md", "text/csv": ".csv",
    "text/plain": ".txt",
}


def _ext(media_type):
    return EXT.get(media_type, ".bin")


def _walk(node, fn):
    """Depth-first rewrite: fn returns a replacement dict, or None to descend."""
    if isinstance(node, dict):
        replaced = fn(node)
        if replaced is not None:
            return replaced
        return {k: _walk(v, fn) for k, v in node.items()}
    if isinstance(node, list):
        return [_walk(v, fn) for v in node]
    return node


def _extract_source(src, media_dir, written, warn):
    """base64 source dict -> reference dict, writing the blob out once."""
    if not (isinstance(src, dict) and src.get("type") == "base64"):
        return None
    data = src.get("data")
    if not isinstance(data, str) or not data:
        return None
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as e:
        # Leave the block exactly as it was: a backup must not lose data it
        # failed to understand.
        warn.append(f"undecodable base64 ({e}); left inline")
        return None

    media_type = src.get("media_type") or "application/octet-stream"
    sha = hashlib.sha256(raw).hexdigest()
    name = sha[:16] + _ext(media_type)
    path = os.path.join(media_dir, name)
    if name not in written:
        if not os.path.exists(path) or os.path.getsize(path) != len(raw):
            os.makedirs(media_dir, exist_ok=True)
            with open(path, "wb") as f:
                f.write(raw)
        written.add(name)

    ref = {k: v for k, v in src.items() if k != "data"}
    ref.update({"type": REF_TYPE, "media_type": media_type,
                "path": "media/" + name, "bytes": len(raw), "sha256": sha})
    return ref


def _restore_source(ref, media_dir, warn):
    if not (isinstance(ref, dict) and ref.get("type") == REF_TYPE):
        return None
    path = os.path.join(media_dir, os.path.basename(ref.get("path", "")))
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        warn.append(f"missing media {ref.get('path')}: {e}")
        return None
    out = {k: v for k, v in ref.items() if k not in ("path", "bytes", "sha256")}
    out["type"] = "base64"
    out["data"] = base64.b64encode(raw).decode("ascii")
    return out


def _convert(src_jsonl, dst_jsonl, media_dir, fn):
    """Rewrite only the lines that carry media; copy the rest byte-for-byte.

    Untouched lines stay identical so re-running produces a near-empty git diff.
    """
    warn, written, changed = [], set(), 0
    os.makedirs(os.path.dirname(dst_jsonl) or ".", exist_ok=True)
    with open(src_jsonl, "rb") as fin, open(dst_jsonl, "wb") as fout:
        for line in fin:
            if b'"data"' not in line and REF_TYPE.encode() not in line:
                fout.write(line)
                continue
            try:
                doc = json.loads(line)
            except ValueError:
                fout.write(line)  # not JSON we understand - keep verbatim
                continue
            new = _walk(doc, lambda n: fn(n, media_dir, warn, written))
            if new == doc:
                fout.write(line)
                continue
            changed += 1
            fout.write(json.dumps(new, ensure_ascii=False,
                                  separators=(",", ":")).encode("utf-8") + b"\n")
    return changed, len(written), warn


def extract(src, dst, media_dir):
    return _convert(src, dst, media_dir,
                    lambda n, m, w, s: _extract_source(n, m, s, w))


def restore(src, dst, media_dir):
    return _convert(src, dst, media_dir,
                    lambda n, m, w, s: _restore_source(n, m, w))


def sync(projects_root, dest_chats):
    """Back up every transcript under projects_root, media split out.

    Transcripts are append-only, so a destination newer than its source is
    already current and is skipped - that keeps a re-run to a few seconds.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import names

    done = skipped = blobs = 0
    all_warn = []
    try:
        slugs = sorted(os.listdir(projects_root))
    except OSError as e:
        sys.exit(f"cannot read {projects_root}: {e}")

    for slug in slugs:
        projdir = os.path.join(projects_root, slug)
        if not os.path.isdir(projdir):
            continue
        clean = names.resolve(slug)
        for fname in sorted(os.listdir(projdir)):
            if not fname.endswith(".jsonl"):
                continue
            sid = fname[: -len(".jsonl")]
            src = os.path.join(projdir, fname)
            dst = os.path.join(dest_chats, clean, fname)
            media_dir = os.path.join(dest_chats, clean, sid, "media")
            try:
                if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                    skipped += 1
                    continue
                _, n, warn = extract(src, dst, media_dir)
            except OSError as e:
                all_warn.append(f"{clean}/{fname}: {e}")
                continue
            blobs += n
            done += 1
            all_warn += [f"{clean}/{fname}: {w}" for w in warn]

            # Sidecar files Claude Code keeps beside the transcript
            # (custom-title.json and friends) - copied, never media-stripped.
            side = os.path.join(projdir, sid)
            if os.path.isdir(side):
                out = os.path.join(dest_chats, clean, sid)
                os.makedirs(out, exist_ok=True)
                for f in os.listdir(side):
                    s, d = os.path.join(side, f), os.path.join(out, f)
                    if os.path.isfile(s) and not (
                        os.path.exists(d) and os.path.getmtime(d) >= os.path.getmtime(s)
                    ):
                        with open(s, "rb") as a, open(d, "wb") as b:
                            b.write(a.read())

    print(f"  transcripts: {done} updated, {skipped} already current")
    print(f"  media files: {blobs} written")
    for w in all_warn[:20]:
        print(f"  WARN {w}")
    if len(all_warn) > 20:
        print(f"  ... and {len(all_warn) - 20} more warnings")
    return len(all_warn)


def _self_test():
    """Round-trip: a repeated blob is stored once and restores byte-identical."""
    import tempfile, shutil
    tmp = tempfile.mkdtemp()
    try:
        png = bytes(range(256)) * 8          # 2 KB of non-text bytes
        pdf = b"%PDF-1.4 fake"
        b64 = base64.b64encode(png).decode()
        lines = [
            {"type": "user", "cwd": "/x", "message": {"content": [
                {"type": "text", "text": "look"},
                {"type": "image", "source": {"type": "base64",
                                             "media_type": "image/png", "data": b64}}]}},
            # same image again on a later turn - must NOT create a second file
            {"type": "user", "message": {"content": [
                {"type": "image", "source": {"type": "base64",
                                             "media_type": "image/png", "data": b64}}]}},
            # a non-image attachment, and an undecodable blob that must survive
            {"type": "user", "message": {"content": [
                {"type": "document", "source": {"type": "base64",
                                                "media_type": "application/pdf",
                                                "data": base64.b64encode(pdf).decode()}},
                {"type": "image", "source": {"type": "base64",
                                             "media_type": "image/png", "data": "!!not base64!!"}}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}},
        ]
        src = os.path.join(tmp, "s.jsonl")
        with open(src, "w") as f:
            for d in lines:
                f.write(json.dumps(d, separators=(",", ":")) + "\n")

        mid, mdir = os.path.join(tmp, "out.jsonl"), os.path.join(tmp, "media")
        changed, nblobs, warn = extract(src, mid, mdir)
        files = sorted(os.listdir(mdir))
        assert len(files) == 2, f"expected 2 media files (png+pdf), got {files}"
        assert nblobs == 2, nblobs
        assert any(f.endswith(".png") for f in files), files
        assert any(f.endswith(".pdf") for f in files), files
        assert len(warn) == 1 and "undecodable" in warn[0], warn
        assert os.path.getsize(mid) < os.path.getsize(src), "transcript did not shrink"
        text = open(mid).read()
        assert b64 not in text, "base64 still inline after extract"
        assert '"text":"look"' in text, "conversation text was lost"

        back = os.path.join(tmp, "back.jsonl")
        restore(mid, back, mdir)
        orig = [json.loads(l) for l in open(src)]
        rt = [json.loads(l) for l in open(back)]
        assert orig == rt, "round-trip changed the transcript"
        print("self-test passed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--self-test"]:
        _self_test()
    elif len(args) == 3 and args[0] == "sync":
        sys.exit(1 if sync(args[1], args[2]) else 0)
    elif len(args) == 4 and args[0] in ("extract", "restore"):
        fn = extract if args[0] == "extract" else restore
        changed, n, warn = fn(args[1], args[2], args[3])
        print(f"{args[0]}: {changed} lines rewritten, {n} media files")
        for w in warn:
            print(f"  WARN {w}")
    else:
        print(__doc__)
        sys.exit(2)
