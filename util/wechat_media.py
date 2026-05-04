"""微信正文 HTML 中的配图发现与下载（MVP：文末图集，落盘到 images/posts/<stem>/）。

不依赖特定 harness；仅标准库。调用方传入页面 URL 作 Referer 以绕过常见防盗链。
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[misc, assignment]

import urllib.error
import urllib.request

UA_WECHAT_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50(0x1800323d) "
    "NetType/WIFI Language/zh_CN"
)

_ALLOWED_NETLOCS = frozenset(
    {
        "mmbiz.qpic.cn",
        "mmbiz.qlogo.cn",
        "wx.qlogo.cn",
    }
)

_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR_RE = re.compile(r'\b(data-src|src)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_WX_FMT_RE = re.compile(r"wx_fmt=([a-z0-9]+)", re.IGNORECASE)


def _normalize_img_url(raw: str) -> str:
    u = (raw or "").strip()
    if not u or u.startswith("data:") or u.startswith("javascript:"):
        return ""
    if u.startswith("//"):
        u = "https:" + u
    if not u.startswith("http"):
        return ""
    try:
        from urllib.parse import urlparse

        host = (urlparse(u).hostname or "").lower()
    except Exception:
        return ""
    if host not in _ALLOWED_NETLOCS:
        return ""
    return u


def discover_wechat_image_urls(html: str) -> list[str]:
    """按出现顺序返回去重后的白名单图片 URL。"""
    out: list[str] = []
    seen: set[str] = set()
    for m in _IMG_TAG_RE.finditer(html or ""):
        tag = m.group(0)
        data_src = src = ""
        for am in _ATTR_RE.finditer(tag):
            name, val = am.group(1).lower(), am.group(2)
            if name == "data-src":
                data_src = val
            elif name == "src":
                src = val
        cand = _normalize_img_url(data_src) or _normalize_img_url(src)
        if not cand or cand in seen:
            continue
        seen.add(cand)
        out.append(cand)
    return out


def _ext_from_url_or_ct(url: str, content_type: str | None) -> str:
    m = _WX_FMT_RE.search(url)
    if m:
        e = m.group(1).lower()
        if e in ("jpeg", "jpg", "png", "gif", "webp", "bmp"):
            return "jpg" if e == "jpeg" else e
    ct = (content_type or "").lower()
    if "png" in ct:
        return "png"
    if "gif" in ct:
        return "gif"
    if "webp" in ct:
        return "webp"
    if "jpeg" in ct or "jpg" in ct:
        return "jpg"
    return "png"


def _fetch_bytes(
    url: str,
    *,
    referer: str,
    max_bytes: int,
    timeout: int = 60,
) -> tuple[bytes | None, str | None]:
    headers = {
        "User-Agent": UA_WECHAT_MOBILE,
        "Referer": referer or "https://mp.weixin.qq.com/",
    }
    if requests is not None:
        try:
            r = requests.get(url, headers=headers, timeout=timeout, stream=True)
            r.raise_for_status()
            ct = r.headers.get("Content-Type")
            data = r.content[: max_bytes + 1]
        except OSError as e:
            print(f"[wechat_media] WARN skip download {url!r}: {e}", flush=True)
            return None, None
    else:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ct = resp.headers.get("Content-Type")
                data = resp.read(max_bytes + 1)
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f"[wechat_media] WARN skip download {url!r}: {e}", flush=True)
            return None, None
    if len(data) > max_bytes:
        print(f"[wechat_media] WARN skip {url!r}: size {len(data)} > max {max_bytes}", flush=True)
        return None, None
    return data, ct


def extract_and_download_gallery(
    html: str,
    *,
    page_url: str,
    root: Path,
    post_stem: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> tuple[int, list[str]]:
    """下载微信配图并生成文末图集 Markdown 行（相对 posts/*.html 的路径）。

    返回 (成功张数, [ '![](../images/posts/<stem>/001.png)', ... ] )。
    """
    urls = discover_wechat_image_urls(html)
    if not urls:
        return 0, []

    dest_dir = root / "images" / "posts" / post_stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    ok = 0
    for i, url in enumerate(urls, start=1):
        data, ct = _fetch_bytes(url, referer=page_url, max_bytes=max_bytes)
        if not data:
            continue
        ext = _ext_from_url_or_ct(url, ct)
        fname = f"{i:03d}.{ext}"
        out_path = dest_dir / fname
        out_path.write_bytes(data)
        rel = f"../images/posts/{post_stem}/{fname}"
        lines.append(f"![]({rel})")
        ok += 1
    return ok, lines
