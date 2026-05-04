"""测试 PR T2.2: extract_ps 保留章节序号 + 紧邻短标题。

行为契约:
- "01" / "02" / 任意 1-2 位数字独立成段 → 保留(章节序号)
- 章节序号后紧邻 ≤ 20 字的短段 → 保留(章节标题)
- 长段(>10 字) → 保留(原行为)
- 其它 ≤ 10 字短段 → 丢弃(原行为)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(ROOT / "util"))

from annotate_lib import extract_ps  # noqa: E402


def _wrap(*paragraphs: str) -> str:
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return f"<html><body>{body}</body></html>"


class TestChapterRetention(unittest.TestCase):
    def test_chapter_number_alone_kept(self) -> None:
        """独立的 '01' 应被保留(章节序号)。"""
        html = _wrap("01", "这是足够长的正文段落，应当被保留下来。")
        out = extract_ps(html, warn=False)
        self.assertIn("01", out, f"章节序号 '01' 应保留,实际:{out}")

    def test_chapter_number_double_digit_kept(self) -> None:
        """'02'/'10'/'99' 等 1-2 位数字都应保留。"""
        for num in ("02", "10", "99"):
            html = _wrap(num, "正文段落足够长以满足保留阈值。")
            out = extract_ps(html, warn=False)
            with self.subTest(num=num):
                self.assertIn(num, out)

    def test_chapter_title_after_num_kept(self) -> None:
        """紧跟章节序号的短标题应保留。"""
        html = _wrap(
            "01",
            "什么是赛博朋克",  # 8 字,正常会被丢
            "正文足够长内容,论述充分有力,展开主题。",
        )
        out = extract_ps(html, warn=False)
        self.assertIn("什么是赛博朋克", out, f"章节标题应保留,实际:{out}")

    def test_chapter_title_at_threshold_kept(self) -> None:
        """长度 = 10 字(刚好等于 _EXTRACT_PS_MIN_LEN)的章节标题应保留。"""
        title = "做IP，本质是在灭火"  # 10 字符
        self.assertEqual(len(title), 10)
        html = _wrap("02", title, "充分的正文段落,继续展开论述与举例。")
        out = extract_ps(html, warn=False)
        self.assertIn(title, out)

    def test_long_paragraph_alone_still_kept(self) -> None:
        """与章节无关的长段照常保留(原行为不变)。"""
        long = "这是一个完全独立的长段落,与章节序号无关,但长度足够。"
        html = _wrap(long)
        out = extract_ps(html, warn=False)
        self.assertEqual(out, [long])

    def test_short_text_without_chapter_context_still_dropped(self) -> None:
        """非章节上下文中的短段仍然丢弃(避免误保留运营段)。"""
        html = _wrap("点赞关注", "正文足够长继续展开论述...")
        out = extract_ps(html, warn=False)
        self.assertNotIn("点赞关注", out, f"非章节上下文短段应丢弃,实际:{out}")

    def test_only_one_short_kept_after_chapter(self) -> None:
        """章节序号后只保留**第一个**短段(避免连续误保留)。"""
        html = _wrap(
            "01",
            "什么是赛博朋克",  # 应保留(标题)
            "短句2",  # 应丢弃(非紧邻 num)
            "正文段足够长继续展开论述。",
        )
        out = extract_ps(html, warn=False)
        self.assertIn("什么是赛博朋克", out)
        self.assertNotIn("短句2", out, f"非紧邻 num 的短句应丢弃,实际:{out}")

    def test_chapter_num_resets_after_long_paragraph(self) -> None:
        """章节序号 + 长段 + 短段 → 短段应丢弃(因为长段重置了状态)。"""
        html = _wrap(
            "01",
            "这是一段足够长的章节正文,描述了赛博朋克的核心要素。",
            "短段X",  # 应丢弃
            "另一段足够长的论述。",
        )
        out = extract_ps(html, warn=False)
        self.assertNotIn("短段X", out, f"长段后再短段应丢弃,实际:{out}")

    def test_three_digit_number_not_treated_as_chapter(self) -> None:
        """3 位数字不被视为章节序号(避免误保留过多)。"""
        html = _wrap("123", "正文段落足够长继续展开论述。")
        out = extract_ps(html, warn=False)
        self.assertNotIn("123", out, "3 位数字不应被视为章节序号")

    def test_tencent_article_real_pattern(self) -> None:
        """复现 tencent 篇真实模式:01/02 + 章节标题 + 长正文。"""
        html = _wrap(
            "如何从零构建一个IP？",
            "01",
            "什么是赛博朋克",
            "赛博朋克这个词由 Cyber 和 Punk 组成,内核是技术与反叛的混合。",
            "02",
            "做IP，本质是在灭火",
            "这一节展开如何在有限时间和预算下管理设计决策的优先级。",
        )
        out = extract_ps(html, warn=False)
        for expect in ("01", "什么是赛博朋克", "02", "做IP，本质是在灭火"):
            self.assertIn(expect, out, f"应保留 {expect!r},实际:{out}")


if __name__ == "__main__":
    unittest.main()
