"""util/wechat_media：微信配图 URL 发现（无网络）。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(ROOT / "util"))
import wechat_media as wm  # noqa: E402


class TestWechatMedia(unittest.TestCase):
    def test_discover_ordered_dedupe(self) -> None:
        html = """
        <p><img data-src="https://mmbiz.qpic.cn/a/1?wx_fmt=png" src="https://mmbiz.qpic.cn/a/1?wx_fmt=png"/></p>
        <img data-src="https://mmbiz.qpic.cn/b/2?wx_fmt=jpeg" />
        """
        urls = wm.discover_wechat_image_urls(html)
        self.assertEqual(
            urls,
            [
                "https://mmbiz.qpic.cn/a/1?wx_fmt=png",
                "https://mmbiz.qpic.cn/b/2?wx_fmt=jpeg",
            ],
        )

    def test_reject_non_whitelist(self) -> None:
        html = '<img data-src="https://evil.example/x.png"/>'
        self.assertEqual(wm.discover_wechat_image_urls(html), [])
