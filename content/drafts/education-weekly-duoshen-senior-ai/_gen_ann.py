#!/usr/bin/env python3
"""从同目录 terms.json 生成 llm_annotations.json（便于 diff / 人工核对）。

正式出 HTML 请用 meta.annotate_engine=terms_json，由 build_draft 直接读 terms.json，
不必依赖本脚本产物。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "workflow"))
sys.path.insert(0, str(ROOT / "util"))

from md_split import paragraphs_from_markdown
import annotate_merge as am

DRAFT = Path(__file__).resolve().parent


def main() -> None:
    md = (DRAFT / "01-source.md").read_text(encoding="utf-8")
    paras = paragraphs_from_markdown(md)
    rows = json.loads((DRAFT / "terms.json").read_text(encoding="utf-8"))
    payload = am.build_payload_from_terms_rows(paras, rows)
    (DRAFT / "llm_annotations.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    n = len(payload["annotations"])
    hit = sum(1 for a in payload["annotations"] if "skip" not in a)
    print("sentences", n, "annotated", hit)


if __name__ == "__main__":
    main()
