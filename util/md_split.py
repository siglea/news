"""Split 01-source.md into paragraph strings for annotation."""
from __future__ import annotations

import re


def paragraphs_from_markdown(md: str) -> list[str]:
    md = md.strip()
    if not md:
        return []
    blocks = re.split(r"\n\s*\n+", md)
    out: list[str] = []
    for block in blocks:
        lines: list[str] = []
        for line in block.split("\n"):
            s = line.strip()
            if not s:
                continue
            s = re.sub(r"^#+\s*", "", s)
            lines.append(s)
        if not lines:
            continue
        para = "\n".join(lines).strip()
        if len(para) > 3:
            out.append(para)
    return out
