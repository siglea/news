#!/usr/bin/env python3
"""
Step 2–3: 01-source.md + meta.json -> 02-annotate-tasks.json + posts/*.html

必须存在 `llm_annotations.json`（或 meta.llm_annotations_file）；由 `export-chat-bundle` + 大模型
按 `util/prompts/chat_annotate_system.txt` 产出。缺失则 build 失败。
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from paths import ROOT, UTIL_DIR
from validate import check_adjacent_in_html

sys.path.insert(0, str(UTIL_DIR))
from md_split import paragraphs_from_markdown

import annotate_lib as al


def build_slug(slug: str, *, skip_validate: bool = False) -> Path:
    draft = ROOT / "content" / "drafts" / slug
    meta_path = draft / "meta.json"
    src_path = draft / "01-source.md"
    if not meta_path.is_file():
        raise SystemExit(f"missing {meta_path}")
    if not src_path.is_file():
        raise SystemExit(f"missing {src_path}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    md = src_path.read_text(encoding="utf-8")
    paras_text = paragraphs_from_markdown(md)

    tasks = {
        "version": 1,
        "slug": slug,
        "paragraphs": [],
    }
    ann_name = meta.get("llm_annotations_file", "llm_annotations.json")
    ann_path = draft / ann_name

    if not ann_path.is_file():
        raise SystemExit(
            f"missing {ann_path}: run `python3 workflow/mingox.py export-chat-bundle --slug {slug}`, "
            "give an LLM the bundle's system_prompt + sentences, save JSON per "
            "docs/steps/02-annotate.md, then build again."
        )

    import annotate_merge as am

    payload = json.loads(ann_path.read_text(encoding="utf-8"))
    paras_html_parts, dbg = am.apply_annotations_payload(paras_text, payload)
    print("annotate_merge", dbg, file=sys.stderr)

    for i, ptxt in enumerate(paras_text):
        html_p = (
            paras_html_parts[i]
            if i < len(paras_html_parts)
            else f"<p>{html.escape(ptxt)}</p>"
        )
        tasks["paragraphs"].append({"index": i, "source_text": ptxt, "html": html_p})

    paras_html = "\n\n".join(paras_html_parts)
    tasks_path = draft / "02-annotate-tasks.json"
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", tasks_path)

    if not skip_validate:
        bad = check_adjacent_in_html(paras_html)
        if bad:
            print("FAIL: adjacent word-block in generated article body", file=sys.stderr)
            for ln, s in bad:
                print(f"  {ln}: {s}", file=sys.stderr)
            raise SystemExit(1)

    tbody = al.vocab_tbody_html(paras_html)
    ft = meta.get("footer_template", "verbatim")
    rb2 = meta.get("risk_blurb_secondary")
    out = al.build_post_html(
        paras_html=paras_html,
        tbody=tbody,
        title_zh=meta["title_zh"],
        title_en=meta["title_en"],
        url=meta.get("source_url") or "",
        meta_description=meta.get("meta_description", ""),
        source_account=meta.get("source_account", al.DEFAULT_SOURCE_ACCOUNT),
        omit_sections_note=meta.get("omit_sections_note", al.DEFAULT_OMIT_SECTIONS_NOTE),
        risk_blurb=meta.get("risk_blurb", al.DEFAULT_RISK_BLURB),
        title_emoji=meta.get("title_emoji", "📈"),
        include_source_footer=bool(meta.get("include_source_footer", True)),
        footer_template=ft if ft in ("verbatim", "derivative") else "verbatim",
        source_author_display=meta.get("source_author_display", "") or "",
        footer_derivative_mp_unknown=bool(meta.get("footer_derivative_mp_unknown", False)),
        risk_blurb_secondary=rb2 if isinstance(rb2, str) and rb2.strip() else None,
    )
    out_path = ROOT / meta["out_html"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print("wrote", out_path, "vocab", len(al.extract_vocab_rows(paras_html)))
    return out_path


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Build post from content/drafts/<slug>/")
    ap.add_argument("slug")
    ap.add_argument("--skip-validate", action="store_true")
    a = ap.parse_args()
    build_slug(a.slug, skip_validate=a.skip_validate)
