#!/usr/bin/env python3
"""Find likely real secrets (keys/tokens) in a folder before it gets uploaded.

Usage:
  python3 scan_secrets.py <folder>    # exit 1 and list files if anything is found
  python3 scan_secrets.py --self-test # check the rules still work

Skips things that look like secrets but aren't: AWS key IDs inside pre-signed
S3 links (an ID alone is not a secret), and obvious fakes from docs and tests
(all zeros, repeated chars, "EXAMPLE", 0123456789ABCDEF-style runs).
"""
import os, random, re, string, sys

PATTERNS = [
    ("AWS access key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[pousr]_[0-9A-Za-z]{36}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9]{6,}-[0-9A-Za-z-]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    # Only a header followed by real key material counts; a header mentioned in text doesn't.
    ("private key", re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----"
        r"(?:\\+n|\s)+[A-Za-z0-9+/=]{40,}")),
]

def looks_fake(value: str) -> bool:
    body = re.sub(r"^(AKIA|gh[pousr]_|xox[baprs]-|AIza)", "", value)
    body = re.sub(r"[^A-Za-z0-9]", "", body)
    if "example" in body.lower() or len(set(body)) <= 4:
        return True
    # Runs like abcdef... / 0123456789ABCDEF: real tokens are random, so
    # consecutive characters almost never follow each other.
    steps = sum(1 for a, b in zip(body, body[1:]) if ord(b) == ord(a) + 1)
    return len(body) > 1 and steps / (len(body) - 1) > 0.5

def findings(text: str):
    for name, pat in PATTERNS:
        for m in pat.finditer(text):
            value = m.group(0)
            if name == "AWS access key ID" and text[max(0, m.start() - 12):m.start()].endswith("Credential="):
                continue  # key ID inside a pre-signed S3 link
            if name != "private key" and looks_fake(value):
                continue
            yield name, value

def scan(root: str):
    hits = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            path = os.path.join(dirpath, f)
            try:
                with open(path, errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            for name, value in findings(text):
                hits.append((os.path.relpath(path, root), name, value[:8] + "…"))
                break
    return hits

def self_test():
    rnd = random.Random(7)
    def rand(chars, n):
        return "".join(rnd.choice(chars) for _ in range(n))
    up, alnum = string.ascii_uppercase + string.digits, string.ascii_letters + string.digits
    real = {  # built at runtime so no realistic-looking secret is ever committed
        "aws": "key = AKIA" + rand(up, 16),
        "github": "token gh" + "p_" + rand(alnum, 36),
        "slack": "xox" + "b-" + rand(string.digits, 12) + "-" + rand(string.digits, 12) + "-" + rand(alnum, 24),
        "pem": "-----BEGIN RSA " + "PRIVATE KEY-----\\n" + rand(alnum + "+/", 64),
    }
    fake = {
        "zeros": "AKIA" + "0" * 16,
        "aws docs": "AKIA" + "IOSFODNN7EXAMPLE",
        "sequence": "AKIA" + "0123456789ABCDEF",
        "alphabet": "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123456789",
        "repeat": "gh" + "p_" + "a" * 36,
        "short slack": "xox" + "b-1234-abcd-EFGH",
        "presigned": "s3.jpeg?X-Amz-Credential=AKIA" + rand(up, 16) + "%2F20260923",
        "pem mention": "your private key starts with `-----BEGIN OPENSSH " + "PRIVATE KEY-----`, never paste it",
        "pem fixture": "-----BEGIN RSA " + "PRIVATE KEY-----\\nabc\\n",
    }
    for k, v in real.items():
        assert list(findings(v)), f"missed real secret: {k}"
    for k, v in fake.items():
        assert not list(findings(v)), f"false alarm: {k}"
    print("self-test passed")

if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        sys.exit(0)
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    hits = scan(sys.argv[1])
    for path, name, preview in hits:
        print(f"  possible {name} in: {path}  ({preview})")
    sys.exit(1 if hits else 0)
