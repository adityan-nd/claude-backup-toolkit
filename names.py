#!/usr/bin/env python3
"""Resolve Claude Code's internal project-path slug into a clean, readable folder name.

Edit STATIC_MAP below with your own repos — see docs/04-naming.md.
"""
import re, sys

STATIC_MAP = {
    # "-Users-you-Documents-SourceCode-my-repo": "my-repo",
}

SCRATCH_RE = re.compile(r"(scratch-\d{4}-\d{2}-\d{2}-[0-9a-f]+)$")

def resolve(slug: str) -> str:
    if slug in STATIC_MAP:
        return STATIC_MAP[slug]
    m = SCRATCH_RE.search(slug)
    if m:
        return m.group(1)
    return slug  # unknown slug: keep as-is rather than guess wrong

if __name__ == "__main__":
    print(resolve(sys.argv[1]))
