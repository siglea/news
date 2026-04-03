#!/usr/bin/env python3
"""
Playwright 抓取：适用于简单 HTTP 失败或明显反爬的页面（尤其是微信公众号 mp.weixin.qq.com）。
建议微信链接加 --mobile（模拟 iPhone 内微信 UA），桌面 Chromium 易进「环境异常」验证页。
默认 page.goto 使用 domcontentloaded；可用 --wait-verify SEC 在非 headless 下等待人工点验证。
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

UA_DESKTOP = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
# 微信页在移动端 UA 下常直接出正文，桌面 UA 易进「环境异常」
UA_MOBILE_WECHAT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50(0x1800323d) "
    "NetType/WIFI Language/zh_CN"
)


def fetch_page(
    url: str,
    *,
    headless: bool,
    slow_mo_ms: int,
    mobile: bool,
    wait_verify_sec: int,
    goto_wait_until: str,
) -> tuple[str | None, str | None, str | None]:
    title = author = content = None
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo_ms,
            args=["--disable-blink-features=AutomationControlled"],
        )
        if mobile:
            context = browser.new_context(
                user_agent=UA_MOBILE_WECHAT,
                viewport={"width": 390, "height": 844},
                device_scale_factor=3,
                locale="zh-CN",
                has_touch=True,
            )
        else:
            context = browser.new_context(
                user_agent=UA_DESKTOP,
                viewport={"width": 1280, "height": 900},
                locale="zh-CN",
            )
        page = context.new_page()
        try:
            page.goto(url, timeout=180_000, wait_until=goto_wait_until)
            time.sleep(random.uniform(1.5, 3.0))

            verify_btn = page.locator("#js_verify")
            if wait_verify_sec > 0 and verify_btn.count() > 0:
                print(
                    f"检测到验证页，等待最多 {wait_verify_sec}s（请在浏览器窗口内完成验证）…",
                    file=sys.stderr,
                )
                deadline = time.monotonic() + wait_verify_sec
                while time.monotonic() < deadline:
                    if page.locator("#js_content").count() > 0:
                        try:
                            if page.locator("#js_content").inner_html(timeout=2000):
                                break
                        except Exception:
                            pass
                    time.sleep(2.0)
                time.sleep(1.0)

            page.wait_for_selector("#js_content", timeout=90_000, state="attached")
            time.sleep(random.uniform(0.5, 1.5))
            title = page.locator(".rich_media_title").first.inner_text(timeout=15_000).strip()
            author = page.locator("#js_name").first.inner_text(timeout=15_000).strip()
            content = page.locator("#js_content").first.inner_html(timeout=15_000)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
        finally:
            browser.close()
    return title, author, content


def write_output(
    url: str,
    title: str | None,
    author: str | None,
    content: str | None,
    *,
    html_path: Path | None = None,
    meta_path: Path | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html_path = html_path or (OUTPUT_DIR / "last_content.html")
    meta_path = meta_path or (OUTPUT_DIR / "last.meta.json")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "url": url,
        "title": title,
        "author": author,
        "content_html_path": html_path.name,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
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
    parser.add_argument(
        "--out-html",
        type=Path,
        default=None,
        help="Write #js_content HTML here (default: util/.crawl-output/last_content.html).",
    )
    parser.add_argument(
        "--out-meta",
        type=Path,
        default=None,
        help="Write meta JSON here (default: util/.crawl-output/last.meta.json).",
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Use iPhone MicroMessenger-like UA + narrow viewport (often bypasses desktop verify).",
    )
    parser.add_argument(
        "--wait-verify",
        type=int,
        default=0,
        metavar="SEC",
        help="If verify page (#js_verify) appears, wait SEC seconds for manual verification (headed only).",
    )
    parser.add_argument(
        "--goto-wait-until",
        choices=("commit", "domcontentloaded", "load", "networkidle"),
        default="domcontentloaded",
        help="page.goto wait_until (default domcontentloaded; load 易在微信页超时).",
    )
    args = parser.parse_args()

    title, author, content = fetch_page(
        args.url,
        headless=args.headless,
        slow_mo_ms=args.slow_mo,
        mobile=args.mobile,
        wait_verify_sec=args.wait_verify,
        goto_wait_until=args.goto_wait_until,
    )
    if not content:
        print("FAILED: no #js_content (wrong page type, captcha, or selector mismatch).", file=sys.stderr)
        return 1

    meta_path = write_output(
        args.url, title, author, content, html_path=args.out_html, meta_path=args.out_meta
    )
    html_written = args.out_html or (OUTPUT_DIR / "last_content.html")
    print("OK")
    print(f"meta: {meta_path}")
    print(f"html: {html_written}")
    if title:
        print(f"title: {title}")
    if author:
        print(f"author: {author}")
    print(f"content_len: {len(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
