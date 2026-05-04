"""annotate_merge：文末 Markdown 图集段落不参与句索引，并落成 <figure>。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(ROOT / "util"))
import annotate_merge as am  # noqa: E402


class TestGalleryMarkdown(unittest.TestCase):
    def test_paragraph_is_gallery(self) -> None:
        self.assertTrue(
            am.paragraph_is_mingox_gallery_markdown(
                "![](../images/posts/2026-05-04-foo/001.png)\n![](../images/posts/2026-05-04-foo/002.png)"
            )
        )
        self.assertFalse(am.paragraph_is_mingox_gallery_markdown("正文一句。"))
        self.assertFalse(
            am.paragraph_is_mingox_gallery_markdown("![](https://mmbiz.qpic.cn/x.png)")
        )

    def test_flatten_skips_gallery(self) -> None:
        paras = [
            "只有一句中文。",
            "![](../images/posts/x/001.png)",
        ]
        sents, origin = am.flatten_paragraphs(paras)
        self.assertEqual(sents, ["只有一句中文。"])
        self.assertEqual(origin, [(0, 0)])

    def test_figure_html(self) -> None:
        h = am.gallery_markdown_paragraph_to_figure_html(
            "![](../images/posts/x/001.png)\n![图二](../images/posts/x/002.jpg)"
        )
        self.assertIn('class="article-figure"', h)
        self.assertIn("../images/posts/x/001.png", h)
        self.assertIn("../images/posts/x/002.jpg", h)
        self.assertIn('loading="lazy"', h)
