"""Opt-in article body segmentation for `article_layout: segments` in meta.json.

Wraps blocks between `<h2 class="article-subheading">` / `<h3 class="article-subheading">`
into `<section class="article-section">` so CSS can style chapter-like rhythm without
affecting posts that omit `article_layout` or use flat/classic (default).
"""
from __future__ import annotations

import re

# Top-level body blocks emitted by annotate_merge / gallery (no nested <article>)
_BLOCK_RE = re.compile(
    r"(<h2\b[^>]*class=\"article-subheading\"[^>]*>[\s\S]*?</h2>)"
    r"|(<h3\b[^>]*class=\"article-subheading\"[^>]*>[\s\S]*?</h3>)"
    r"|(<figure\b[\s\S]*?</figure>)"
    r"|(<p\b[^>]*>[\s\S]*?</p>)",
    re.IGNORECASE,
)


def wrap_article_sections(body_html: str) -> str:
    """Group content between subheadings into `<section class="article-section">`.

    If there are no subheadings, wraps the entire body in one section (still
    allows segment-scoped padding/background in CSS).
    """
    raw = (body_html or "").strip()
    if not raw:
        return body_html

    blocks: list[str] = []
    pos = 0
    for m in _BLOCK_RE.finditer(raw):
        if m.start() > pos:
            gap = raw[pos : m.start()].strip()
            if gap:
                blocks.append(gap)
        blocks.append(m.group(0).strip())
        pos = m.end()
    if pos < len(raw):
        tail = raw[pos:].strip()
        if tail:
            blocks.append(tail)

    if not blocks:
        return body_html

    sections: list[list[str]] = []
    cur: list[str] = []
    for b in blocks:
        if re.match(r"<h[23]\b", b, re.I):
            if cur:
                sections.append(cur)
            cur = [b]
        else:
            cur.append(b)
    if cur:
        sections.append(cur)

    wrapped = []
    for i, sec in enumerate(sections):
        extra = " article-section--lede" if i == 0 else ""
        inner = "\n\n".join(sec)
        wrapped.append(f'<section class="article-section{extra}">\n{inner}\n</section>')
    return "\n\n".join(wrapped)
