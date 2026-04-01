#!/usr/bin/env python3
"""
Playwright 抓取：适用于简单 HTTP 失败或明显反爬的页面（尤其是微信公众号 mp.weixin.qq.com）。
非交互环境可试 --headless；若仍被拦，请在有图形界面下运行并完成验证。
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).resolve().parent / ".crawl-output"


def fetch_page(url: str, *, headless: bool, slow_mo_ms: int) -> tuple[str | None, str | None, str | None]:
    title = author = content = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=120_000)
            time.sleep(random.uniform(2, 4))
            title = page.locator(".rich_media_title").inner_text().strip()
            author = page.locator("#js_name").inner_text().strip()
            content = page.locator("#js_content").inner_html()
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
        finally:
            browser.close()
    return title, author, content


def write_output(url: str, title: str | None, author: str | None, content: str | None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "url": url,
        "title": title,
        "author": author,
        "content_html_path": "last_content.html",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = OUTPUT_DIR / "last.meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path = OUTPUT_DIR / "last_content.html"
    html_path.write_text(content or "", encoding="utf-8")
    return meta_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Playwright crawl (WeChat article layout).")
    parser.add_argument("--url", required=True, help="Page URL, e.g. mp.weixin.qq.com/s/...")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Headless Chromium (may fail on sites that require visible verification).",
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=300,
        metavar="MS",
        help="Slow down operations by MS milliseconds (default 300).",
    )
    args = parser.parse_args()

    title, author, content = fetch_page(args.url, headless=args.headless, slow_mo_ms=args.slow_mo)
    if not content:
        print("FAILED: no #js_content (wrong page type, captcha, or selector mismatch).", file=sys.stderr)
        return 1

    meta_path = write_output(args.url, title, author, content)
    print("OK")
    print(f"meta: {meta_path}")
    print(f"html: {OUTPUT_DIR / 'last_content.html'}")
    if title:
        print(f"title: {title}")
    if author:
        print(f"author: {author}")
    print(f"content_len: {len(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
