#!/usr/bin/env python3
"""CLI: WeChat js_content + article-profiles.json -> posts/*.html. Logic in annotate_lib."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_util = Path(__file__).resolve().parent
if str(_util) not in sys.path:
    sys.path.insert(0, str(_util))

import annotate_lib as al


def main() -> None:
    util_dir = Path(__file__).resolve().parent
    root = util_dir.parent
    ap = argparse.ArgumentParser(description="WeChat js_content -> annotated post HTML")
    ap.add_argument(
        "--profile",
        default=None,
        help="key in util/article-profiles.json (default: file's default_profile)",
    )
    args = ap.parse_args()
    cfg_path = util_dir / "article-profiles.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    profile_name = args.profile or cfg.get("default_profile")
    if not profile_name:
        raise SystemExit("set default_profile in article-profiles.json or pass --profile")
    profiles = cfg.get("profiles") or {}
    if profile_name not in profiles:
        raise SystemExit(f"unknown profile {profile_name!r}; known: {sorted(profiles)}")
    profile = profiles[profile_name]

    src = root / profile["crawl_js"]
    if not src.is_file():
        raise SystemExit(f"missing crawl input: {src}")

    html_in = src.read_text(encoding="utf-8")
    chunks = al.extract_ps(html_in)
    body_chunks = al.slice_body_chunks(
        chunks,
        profile.get("body_end_marker"),
        profile.get("body_paragraph_cap"),
    )

    eng = profile.get("annotate_engine", "keywords")
    if eng == "chat_json":
        import annotate_merge as am

        rel = profile.get("llm_annotations_file")
        if not rel or not isinstance(rel, str):
            raise SystemExit("annotate_engine=chat_json requires string llm_annotations_file in profile (path relative to repo root)")
        ann_path = root / rel
        if not ann_path.is_file():
            raise SystemExit(f"annotate_engine=chat_json: missing {ann_path}")
        payload = json.loads(ann_path.read_text(encoding="utf-8"))
        parts, dbg = am.apply_annotations_payload(body_chunks, payload)
        paras_html = "\n\n".join(parts)
        print("annotate_engine=chat_json", dbg, file=sys.stderr)
    elif eng == "keywords":
        used_en: set[str] = set()
        paras_html = "\n\n".join(al.annotate_paragraph(c, used_en) for c in body_chunks)
    else:
        hint = ' 原 "llm" 已删除，请改用 "chat_json" 并设置 llm_annotations_file。' if eng == "llm" else ""
        raise SystemExit(f"unknown annotate_engine={eng!r}; use \"keywords\" or \"chat_json\".{hint}")
    tbody = al.vocab_tbody_html(paras_html)

    ft = profile.get("footer_template", "verbatim")
    rb2 = profile.get("risk_blurb_secondary")
    out = al.build_post_html(
        paras_html=paras_html,
        tbody=tbody,
        title_zh=profile["title_zh"],
        title_en=profile["title_en"],
        url=profile["source_url"],
        meta_description=profile.get("meta_description", ""),
        source_account=profile.get("source_account", al.DEFAULT_SOURCE_ACCOUNT),
        omit_sections_note=profile.get("omit_sections_note", al.DEFAULT_OMIT_SECTIONS_NOTE),
        risk_blurb=profile.get("risk_blurb", al.DEFAULT_RISK_BLURB),
        title_emoji=profile.get("title_emoji", "📈"),
        include_source_footer=profile.get("include_source_footer", True),
        footer_template=ft if ft in ("verbatim", "derivative") else "verbatim",
        source_author_display=profile.get("source_author_display", "") or "",
        footer_derivative_mp_unknown=bool(profile.get("footer_derivative_mp_unknown", False)),
        risk_blurb_secondary=rb2 if isinstance(rb2, str) and rb2.strip() else None,
    )
    out_path = root / profile["out_html"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print("profile", profile_name)
    print("wrote", out_path, "paragraphs", len(body_chunks), "vocab", len(al.extract_vocab_rows(paras_html)))


if __name__ == "__main__":
    main()
