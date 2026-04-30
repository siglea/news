#!/usr/bin/env python3
"""
Step 2–3: 01-source.md + meta.json -> 02-annotate-tasks.json + posts/*.html

必须存在 `llm_annotations.json`（或 meta.llm_annotations_file）；由 `export-chat-bundle` + 大模型
按 `util/prompts/chat_annotate_system.txt` 产出。缺失则 build 失败。
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from paths import ROOT, UTIL_DIR
from validate import check_adjacent_in_html

sys.path.insert(0, str(UTIL_DIR))
from md_split import paragraphs_from_markdown

import annotate_lib as al
from annotation_quality_gate import check_quality


# ============================================================
# index.html `<li>` 注入(T-N3 自动化"deploy ≠ 发布完成"硬冲突的根除)
# ============================================================

_INDEX_LI_INDENT = "                    "  # 20 空格,匹配现有 <li> 缩进


def generate_post_li(meta: dict) -> str:
    """从 meta.json 生成一段 `<li class="post-item">` HTML。

    必填字段:title_emoji / title_zh / title_en / date / out_html / meta_description
    可选字段:tags(list[str],缺省时只用 "转载" 一个标签)

    输出格式与现有 index.html `<ul class="post-list">` 内 `<li>` 完全一致(20 空格缩进)。
    """
    emoji = meta.get("title_emoji", "📈")
    title_zh = meta["title_zh"]
    title_en = meta["title_en"]
    date = meta["date"]
    href = meta["out_html"]
    excerpt = meta.get("meta_description", "").strip()
    tags = meta.get("tags") or ["转载"]
    if not isinstance(tags, list):
        tags = [str(tags)]
    tags_str = ", ".join(str(t).strip() for t in tags if str(t).strip())
    if not tags_str:
        tags_str = "转载"

    # title_zh / title_en / excerpt 出现在 HTML 内,需 escape 防 XSS / 渲染错位
    e_emoji = html.escape(emoji)
    e_title_zh = html.escape(title_zh)
    e_title_en = html.escape(title_en)
    e_date = html.escape(date)
    e_href = html.escape(href, quote=True)
    e_excerpt = html.escape(excerpt) if excerpt else "（待补摘要）"
    e_tags = html.escape(tags_str)

    indent = _INDEX_LI_INDENT
    sub = indent + "    "
    sub2 = indent + "        "
    return (
        f'{indent}<li class="post-item">\n'
        f'{sub}<div class="post-title">\n'
        f'{sub2}<a href="{e_href}">{e_emoji} {e_title_zh}<br>'
        f'<small class="title-en">{e_title_en}</small></a>\n'
        f'{sub}</div>\n'
        f'{sub}<div class="post-meta">📅 {e_date} | 📝 双语 | 🏷️ {e_tags}</div>\n'
        f'{sub}<div class="post-excerpt">\n'
        f'{sub2}<a href="{e_href}">{e_excerpt}</a>\n'
        f'{sub}</div>\n'
        f'{indent}</li>'
    )


def _index_already_has_slug(index_text: str, out_html: str) -> bool:
    """index.html 是否已包含指向 `out_html` 的 `<a href>`?"""
    # 用 quote=True 的 escape 形式匹配,避免 / 等字符差异
    needle = f'href="{html.escape(out_html, quote=True)}"'
    return needle in index_text


def inject_li_to_index(index_path: Path, li_html: str, *, dry_run: bool = False) -> dict:
    """在 `index_path` 的 `<ul class="post-list">` 顶部注入 `li_html`。

    幂等:若 li_html 中的 `href` 已在 index 中,跳过注入(返回 inserted=False)。

    返回 dict:`{inserted: bool, reason: str, new_text: str | None}`
    `dry_run=True` 时不写文件,仅返回 new_text 供调用方比对。
    """
    if not index_path.is_file():
        return {"inserted": False, "reason": "index.html missing", "new_text": None}
    text = index_path.read_text(encoding="utf-8")

    # 提取 li_html 里的 href,用于幂等判定
    m = re.search(r'href="([^"]+)"', li_html)
    if not m:
        return {
            "inserted": False,
            "reason": "li_html lacks href; cannot dedupe",
            "new_text": None,
        }
    href = m.group(1)
    if _index_already_has_slug(text, href.replace("&amp;", "&").replace("&#x27;", "'")):
        return {
            "inserted": False,
            "reason": f"index already contains href {href}",
            "new_text": None,
        }

    # 找 `<ul class="post-list">` 行,在其后**直接**插入 li_html
    # (注入位置在 <ul> 之后第一行,即列表顶部)
    pattern = re.compile(r'(<ul class="post-list">)\s*\n', re.MULTILINE)
    if not pattern.search(text):
        return {
            "inserted": False,
            "reason": '<ul class="post-list"> not found',
            "new_text": None,
        }
    new_text = pattern.sub(r"\1\n" + li_html + "\n", text, count=1)
    if not dry_run:
        index_path.write_text(new_text, encoding="utf-8")
    return {"inserted": True, "reason": "ok", "new_text": new_text}


def build_slug(
    slug: str,
    *,
    skip_validate: bool = False,
    skip_quality_gates: bool = False,
    update_index: bool = False,
    dry_run_index: bool = False,
) -> Path:
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

    tasks = {"version": 1, "kind": "annotate_result", "slug": slug, "paragraphs": []}
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
    if not skip_quality_gates:
        all_sents, _ = am.flatten_paragraphs(paras_text)
        q_errors, q_warnings = check_quality(meta, payload, sentences=all_sents)
        for msg in q_warnings:
            print(f"[quality-gate] WARN: {msg}", file=sys.stderr)
        if q_errors:
            print("[quality-gate] FAIL", file=sys.stderr)
            for msg in q_errors:
                print(f"  - {msg}", file=sys.stderr)
            raise SystemExit(1)

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

    if update_index:
        index_path = ROOT / "index.html"
        li_html = generate_post_li(meta)
        if dry_run_index:
            print("[update-index] dry-run preview of <li> to be inserted:")
            print(li_html)
            res = inject_li_to_index(index_path, li_html, dry_run=True)
            print(
                f"[update-index] dry-run result: inserted={res['inserted']} "
                f"reason={res['reason']!r}"
            )
        else:
            res = inject_li_to_index(index_path, li_html, dry_run=False)
            if res["inserted"]:
                print(f"[update-index] OK: inserted <li> for {meta['out_html']}")
            else:
                print(
                    f"[update-index] skipped: {res['reason']}", file=sys.stderr
                )
    return out_path


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Build post from content/drafts/<slug>/")
    ap.add_argument("slug")
    ap.add_argument("--skip-validate", action="store_true")
    ap.add_argument("--skip-quality-gates", action="store_true")
    ap.add_argument(
        "--update-index",
        action="store_true",
        help="生成 <li> 注入 index.html 顶部(默认 off,需显式开启)",
    )
    ap.add_argument(
        "--dry-run-index",
        action="store_true",
        help="与 --update-index 同用:仅预览注入,不动 index.html",
    )
    a = ap.parse_args()
    build_slug(
        a.slug,
        skip_validate=a.skip_validate,
        skip_quality_gates=a.skip_quality_gates,
        update_index=a.update_index,
        dry_run_index=a.dry_run_index,
    )
