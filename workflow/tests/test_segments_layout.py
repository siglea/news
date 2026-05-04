"""Phase 2: segments layout — heading heuristics, section wrap, meta/CLI resolve."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UTIL = ROOT / "util"
WORKFLOW = ROOT / "workflow"
sys.path.insert(0, str(UTIL))
sys.path.insert(0, str(WORKFLOW))

from article_segments import wrap_article_sections  # noqa: E402
import annotate_merge as am  # noqa: E402
from build_draft import resolve_layout_segments  # noqa: E402


class TestHeadingHeuristics(unittest.TestCase):
    def test_h2_enum(self) -> None:
        self.assertEqual(am.paragraph_heading_level("一、认知篇"), 2)
        self.assertEqual(am.paragraph_heading_level("十二、小结"), 2)

    def test_h3_gate_chapter_step(self) -> None:
        self.assertEqual(am.paragraph_heading_level("关卡 1：引言"), 3)
        self.assertEqual(am.paragraph_heading_level("第10章 转折"), 3)
        self.assertEqual(am.paragraph_heading_level("Step 2 准备"), 3)

    def test_h3_num_dot_short(self) -> None:
        self.assertEqual(am.paragraph_heading_level("1. 背景说明"), 3)

    def test_h3_question_legacy(self) -> None:
        self.assertEqual(am.paragraph_heading_level("给婴儿定投半导体龙头？"), 3)

    def test_body_not_heading(self) -> None:
        self.assertEqual(
            am.paragraph_heading_level(
                "在韩国，一种新奇的“婴儿投资”正在年轻父母之间流行起来。"
            ),
            0,
        )
        self.assertEqual(am.paragraph_heading_level("图源：《中央日报》中文网"), 0)

    def test_flatten_skips_headings_when_segments(self) -> None:
        paras = ["一、总览", "正文一句包含足够长度用于分句测试。"]
        sents, origin = am.flatten_paragraphs(paras, layout_segments=True)
        self.assertTrue(all(pi == 1 for pi, _ in origin))


class TestWrapSections(unittest.TestCase):
    def test_wrap_splits_on_h2_and_h3(self) -> None:
        body = (
            "<p>Intro</p>\n"
            '<h2 class="article-subheading">一、A</h2>\n'
            "<p>Mid</p>\n"
            '<h3 class="article-subheading">关卡 1:</h3>\n'
            "<p>Tail</p>"
        )
        out = wrap_article_sections(body)
        self.assertGreaterEqual(out.count("<section"), 3)
        self.assertIn("article-section--lede", out)

    def test_wrap_h3_only(self) -> None:
        body = '<p>a</p>\n<h3 class="article-subheading">b</h3>\n<p>c</p>'
        out = wrap_article_sections(body)
        self.assertGreaterEqual(out.count("<section"), 2)


class TestResolveLayoutSegments(unittest.TestCase):
    def test_default_flat(self) -> None:
        self.assertFalse(resolve_layout_segments({}))
        self.assertFalse(resolve_layout_segments({"article_layout": "flat"}))
        self.assertFalse(resolve_layout_segments({"article_layout": "classic"}))

    def test_segments_meta(self) -> None:
        self.assertTrue(resolve_layout_segments({"article_layout": "segments"}))

    def test_cli_override(self) -> None:
        self.assertTrue(
            resolve_layout_segments({"article_layout": "flat"}, segments_override=True)
        )
        self.assertFalse(
            resolve_layout_segments(
                {"article_layout": "segments"}, segments_override=False
            )
        )


if __name__ == "__main__":
    unittest.main()
