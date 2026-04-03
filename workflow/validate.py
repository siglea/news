#!/usr/bin/env python3
"""Step 2 checks: adjacent word-block (README). Optional density heuristics."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from paths import ROOT

ADJACENT = re.compile(r"</span></span>\s+<span class=\"word-block\"")


def check_adjacent_in_html(html: str, path: str | Path = "") -> list[tuple[int, str]]:
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(html.splitlines(), 1):
        if ADJACENT.search(line):
            bad.append((i, line.strip()[:200]))
    return bad


def validate_file(html_path: Path) -> int:
    text = html_path.read_text(encoding="utf-8")
    bad = check_adjacent_in_html(text, html_path)
    if bad:
        print(f"FAIL adjacent word-block: {html_path}", file=sys.stderr)
        for ln, preview in bad:
            print(f"  line {ln}: {preview}", file=sys.stderr)
        return 1
    print("OK adjacent check:", html_path)
    return 0


def validate_posts_glob() -> int:
    posts = sorted((ROOT / "posts").glob("*.html"))
    code = 0
    for p in posts:
        code |= validate_file(p)
    return code
