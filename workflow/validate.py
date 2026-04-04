#!/usr/bin/env python3
"""Step 2 checks: adjacent word-block (docs/EDITORIAL.md). Optional density heuristics (warn only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from paths import ROOT

ADJACENT = re.compile(r"</span></span>\s+<span class=\"word-block\"")

ARTICLE_RE = re.compile(
    r'<article\s+class="post-content"[^>]*>(.*?)</article>',
    re.DOTALL | re.IGNORECASE,
)
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)


def check_adjacent_in_html(html: str, path: str | Path = "") -> list[tuple[int, str]]:
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(html.splitlines(), 1):
        if ADJACENT.search(line):
            bad.append((i, line.strip()[:200]))
    return bad


def _strip_word_info_and_tags(fragment: str) -> str:
    s = re.sub(r'<span class="word-info">.*?</span>', "", fragment, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def count_sentences_heuristic(plain: str) -> int:
    """Approximate EDITORIAL sentence count: CJK 。！？； outside tags (word-info removed)."""
    if not plain:
        return 0
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", plain))
    if has_cjk:
        parts = [p for p in re.split(r"[。！？；]", plain) if p.strip()]
        return len(parts)
    parts = [p for p in plain.split(";") if p.strip()]
    return len(parts) if parts else 0


def density_warnings_for_html(html: str, source_label: str = "") -> list[str]:
    """
    Heuristic: per <p> in post-content, if estimated sentences > word-block count, emit WARN.
    Does not fail build; align with docs/EDITORIAL.md only approximately (see docs/ANNOTATION.md).
    """
    m = ARTICLE_RE.search(html)
    if not m:
        return []
    inner = m.group(1)
    if not re.search(r'<span class="word-block"', inner):
        return []
    label = str(source_label) if source_label else "?"
    warns: list[str] = []
    for idx, pm in enumerate(P_RE.finditer(inner), 1):
        p_html = pm.group(1)
        n_blocks = len(re.findall(r'<span class="word-block"', p_html))
        plain = _strip_word_info_and_tags(p_html)
        n_sent = count_sentences_heuristic(plain)
        if n_sent <= 0:
            continue
        if n_blocks < n_sent:
            warns.append(
                f"WARN density heuristic: {label} <p>#{idx}: "
                f"~{n_sent} sentence(s) vs {n_blocks} word-block(s) "
                f"(EDITORIAL expects at least one block per sentence; verify manually)"
            )
    return warns


def validate_file(html_path: Path) -> int:
    text = html_path.read_text(encoding="utf-8")
    bad = check_adjacent_in_html(text, html_path)
    if bad:
        print(f"FAIL adjacent word-block: {html_path}", file=sys.stderr)
        for ln, preview in bad:
            print(f"  line {ln}: {preview}", file=sys.stderr)
        return 1
    for w in density_warnings_for_html(text, html_path.name):
        print(w, file=sys.stderr)
    print("OK adjacent check:", html_path)
    return 0


def validate_posts_glob() -> int:
    posts = sorted((ROOT / "posts").glob("*.html"))
    code = 0
    for p in posts:
        code |= validate_file(p)
    return code
