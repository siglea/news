#!/usr/bin/env python3
"""
Step 2–3: 01-source.md + meta.json -> 02-annotate-tasks.json + posts/*.html
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
    paras_html_parts: list[str] = []
    # 仓库约定：默认 chat_json（与 mingox init、docs/ANNOTATION.md 一致）；keywords 须 meta 显式写明
    engine = meta.get("annotate_engine", "chat_json")
    if engine == "chat_json":
        import annotate_merge as am

        ann_name = meta.get("llm_annotations_file", "llm_annotations.json")
        ann_path = draft / ann_name
        if not ann_path.is_file():
            raise SystemExit(
                f"missing {ann_path} (annotate_engine=chat_json).\n"
                f"  1) python3 workflow/mingox.py export-chat-bundle --slug {slug}\n"
                f"  2) 将 bundle 交给任意大模型，按 system_prompt 生成 JSON，保存为上述路径（不必 Cursor）\n"
                f"  3) 再执行 build"
            )
        payload = json.loads(ann_path.read_text(encoding="utf-8"))
        paras_html_parts, dbg = am.apply_annotations_payload(paras_text, payload)
        print("annotate_engine=chat_json", dbg, file=sys.stderr)
        for i, ptxt in enumerate(paras_text):
            html_p = (
                paras_html_parts[i]
                if i < len(paras_html_parts)
                else f"<p>{html.escape(ptxt)}</p>"
            )
            tasks["paragraphs"].append({"index": i, "source_text": ptxt, "html": html_p})
    elif engine == "keywords":
        dedupe = meta.get("keyword_dedupe", True)
        used_en: set[str] | None = set() if dedupe else None
        for i, ptxt in enumerate(paras_text):
            html_p = al.annotate_paragraph(ptxt, used_en)
            tasks["paragraphs"].append({"index": i, "source_text": ptxt, "html": html_p})
            paras_html_parts.append(html_p)
    else:
        hint = (
            ' 原 "llm"（HTTP）已删除，请改用 "chat_json"。' if engine == "llm" else ""
        )
        raise SystemExit(
            f"unknown annotate_engine={engine!r}; use \"keywords\" or \"chat_json\".{hint}"
        )

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
