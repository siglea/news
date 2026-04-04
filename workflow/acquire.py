#!/usr/bin/env python3
"""
Step 1: produce content/drafts/<slug>/01-source.md (+ meta.json updates).
Modes: paste | url | search
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from paths import CONTENT_DRAFTS, ROOT, UTIL_DIR

sys.path.insert(0, str(UTIL_DIR))
import annotate_lib as al


def _draft_dir(slug: str) -> Path:
    d = CONTENT_DRAFTS / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_meta(draft: Path) -> dict:
    p = draft / "meta.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _save_meta(draft: Path, meta: dict) -> None:
    (draft / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _html_to_source_md(html: str) -> str:
    paras = al.extract_ps(html)
    total = sum(len(p) for p in paras)
    if len(paras) < 4 or total < 600:
        plain = al.extract_wechat_plain_paragraphs(html)
        leaf = al.extract_wechat_span_leaf_paragraphs(html)
        plain_n = sum(len(p) for p in plain)
        leaf_n = sum(len(p) for p in leaf)
        if plain_n >= leaf_n and plain_n > total:
            paras = plain
        elif leaf_n > total:
            paras = leaf
    return "\n\n".join(paras)


def acquire_paste(slug: str, body: str, *, meta_updates: dict | None = None) -> Path:
    draft = _draft_dir(slug)
    (draft / "01-source.md").write_text(body.strip() + "\n", encoding="utf-8")
    meta = _load_meta(draft)
    meta.setdefault("slug", slug)
    meta["source_mode"] = "paste"
    if meta_updates:
        meta.update(meta_updates)
    _save_meta(draft, meta)
    print("wrote", draft / "01-source.md")
    return draft / "01-source.md"


def acquire_url(
    slug: str,
    url: str,
    *,
    headless: bool = False,
    wechat_mobile: bool = True,
    wait_verify_sec: int = 0,
) -> Path:
    parsed = urlparse(url)
    draft = _draft_dir(slug)
    if "mp.weixin.qq.com" in (parsed.netloc or ""):
        out_html = UTIL_DIR / ".crawl-output" / f"workflow-{slug}-js_content.html"
        out_meta = UTIL_DIR / ".crawl-output" / f"workflow-{slug}.meta.json"
        for p in (out_html, out_meta):
            if p.exists():
                p.unlink()

        def _run_crawl(extra_args: list[str]) -> int:
            cmd = [
                sys.executable,
                str(UTIL_DIR / "crawl-with-playwright.py"),
                "--url",
                url,
                "--out-html",
                str(out_html),
                "--out-meta",
                str(out_meta),
            ] + extra_args
            if headless:
                cmd.append("--headless")
            if wait_verify_sec > 0:
                cmd.extend(["--wait-verify", str(wait_verify_sec)])
            return subprocess.run(cmd, cwd=str(ROOT)).returncode

        attempts: list[list[str]] = []
        if wechat_mobile:
            attempts.append(["--mobile"])
        attempts.append([])
        last_code = 1
        for extra in attempts:
            print("Playwright:", " ".join(extra) if extra else "(desktop UA)")
            last_code = _run_crawl(extra)
            if last_code == 0 and out_html.is_file() and out_html.stat().st_size > 50:
                break
        if last_code != 0:
            raise SystemExit(
                "Playwright crawl failed (WeChat). 试：去掉 --headless，在本机窗口完成验证；"
                "或加 --wait-verify 180；或 acquire --no-mobile-wechat 仅用桌面 UA。"
            )
        html = out_html.read_text(encoding="utf-8")
        meta_ext = json.loads(out_meta.read_text(encoding="utf-8"))
        body_md = _html_to_source_md(html)
        (draft / "01-source.md").write_text(body_md + "\n", encoding="utf-8")
        m = _load_meta(draft)
        crawled_title = (meta_ext.get("title") or "").strip()
        m.update(
            {
                "slug": slug,
                "source_mode": "url",
                "source_url": url,
                "source_account": meta_ext.get("author") or m.get("source_account") or "微信公众号",
                "title_zh": crawled_title or m.get("title_zh") or slug,
            }
        )
        if m.get("footer_template") == "derivative" and (meta_ext.get("author") or "").strip():
            m["footer_derivative_mp_unknown"] = False
        _save_meta(draft, m)
        print("wrote", draft / "01-source.md")
        return draft / "01-source.md"

    try:
        import trafilatura
    except ImportError as e:
        raise SystemExit(
            "Install workflow deps: pip install -r workflow/requirements.txt"
        ) from e

    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise SystemExit(f"trafilatura failed to download: {url}")
    text = trafilatura.extract(downloaded)
    if not text or len(text) < 80:
        raise SystemExit("Extracted text too short; try Playwright or paste mode.")
    (draft / "01-source.md").write_text(text.strip() + "\n", encoding="utf-8")
    m = _load_meta(draft)
    m.setdefault("slug", slug)
    m["source_mode"] = "url"
    m["source_url"] = url
    _save_meta(draft, m)
    print("wrote", draft / "01-source.md")
    return draft / "01-source.md"


def search_candidates(query: str, *, max_results: int = 8) -> list[dict]:
    try:
        from duckduckgo_search import DDGS
    except ImportError as e:
        raise SystemExit("pip install duckduckgo-search (see workflow/requirements.txt)") from e
    out: list[dict] = []
    with DDGS() as ddgs:
        for i, r in enumerate(ddgs.text(query, max_results=max_results)):
            out.append(
                {
                    "index": i,
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": (r.get("body", "") or "")[:200],
                }
            )
    return out


def acquire_search(slug: str, query: str, pick: int, *, headless: bool = False) -> Path:
    cands = search_candidates(query)
    if pick < 0 or pick >= len(cands):
        raise SystemExit(f"pick must be 0..{len(cands)-1}; got {pick}")
    url = cands[pick]["href"]
    if not url:
        raise SystemExit("empty url for picked result")
    print("using:", url)
    meta = _load_meta(_draft_dir(slug))
    meta["search_query"] = query
    meta["search_pick"] = pick
    _save_meta(_draft_dir(slug), meta)
    return acquire_url(slug, url, headless=headless)


def init_meta_template(
    slug: str,
    *,
    title_zh: str,
    title_en: str,
    out_html: str,
    source_url: str = "",
    title_emoji: str = "📈",
    include_source_footer: bool = False,
    footer_template: str = "verbatim",
    source_author_display: str = "",
    footer_derivative_mp_unknown: bool = False,
    risk_blurb_secondary: str = "",
) -> None:
    draft = _draft_dir(slug)
    meta = {
        "slug": slug,
        "title_zh": title_zh,
        "title_en": title_en,
        "title_emoji": title_emoji,
        "date": date.today().isoformat(),
        "source_url": source_url,
        "source_account": "MingoX",
        "include_source_footer": include_source_footer,
        "footer_template": footer_template
        if footer_template in ("verbatim", "derivative")
        else "verbatim",
        "source_author_display": source_author_display,
        "footer_derivative_mp_unknown": footer_derivative_mp_unknown,
        "out_html": out_html,
        "annotate_engine": "chat_json",
        "meta_description": "",
        "omit_sections_note": "本站已按编辑流程处理正文；具体以原文为准。",
        "risk_blurb": "本文仅供学习交流，不构成投资建议或其他专业意见。",
    }
    if risk_blurb_secondary.strip():
        meta["risk_blurb_secondary"] = risk_blurb_secondary.strip()
    _save_meta(draft, meta)
    print("wrote", draft / "meta.json")
