"""annotation_quality_gate 占位词与假 en 检测（stdlib unittest）。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(ROOT / "util"))


class TestEnPlaceholders(unittest.TestCase):
    def test_lex_variants(self) -> None:
        from annotation_quality_gate import en_suspect_placeholder_or_fake

        for en in (
            "lex",
            "lex0",
            "lex008119",
            "lex049",
            "LEX99",
        ):
            with self.subTest(en=en):
                self.assertTrue(en_suspect_placeholder_or_fake(en), en)

    def test_term_tbd(self) -> None:
        from annotation_quality_gate import en_suspect_placeholder_or_fake

        for en in ("term", "term5", "tbd1", "fixme2"):
            with self.subTest(en=en):
                self.assertTrue(en_suspect_placeholder_or_fake(en), en)
        for en in ("certainly1", "compare2", "molecule1", "data1", "word"):
            with self.subTest(en=en):
                self.assertFalse(en_suspect_placeholder_or_fake(en), en)

    def test_zh_suffix(self) -> None:
        from annotation_quality_gate import en_suspect_placeholder_or_fake

        self.assertTrue(en_suspect_placeholder_or_fake("modelzh"))
        self.assertTrue(en_suspect_placeholder_or_fake("screeningzh"))
        self.assertFalse(en_suspect_placeholder_or_fake("model1"))

    def test_explicit_fake(self) -> None:
        from annotation_quality_gate import en_suspect_placeholder_or_fake

        self.assertTrue(en_suspect_placeholder_or_fake("howcome"))
        self.assertTrue(en_suspect_placeholder_or_fake("postalphafold52"))


class TestZhBoundaryHeuristics(unittest.TestCase):
    def test_short_particle_tail_warn(self) -> None:
        """T-N10 v3:仅 len==2 (单字 + 助词)算 short-zh-tail-particle WARN。"""
        from annotation_quality_gate import zh_boundary_suspect

        body1 = "一场类似次贷危机的风险正在酝酿。"
        # 单字 "机" + 助词 "的" → 2 字 → WARN(切分错位的强信号)
        self.assertEqual(zh_boundary_suspect(body1, "机的"), "short-zh-tail-particle")

    def test_translit_name_right_cut_warn(self) -> None:
        from annotation_quality_gate import zh_boundary_suspect

        body = "对于萨姆·阿尔特曼来说，未来取决于融资。"
        self.assertEqual(zh_boundary_suspect(body, "阿尔特"), "translit-name-right-cut")

    def test_normal_anchor_not_warn(self) -> None:
        from annotation_quality_gate import zh_boundary_suspect

        body = "真实用量成本开始暴露，订阅补贴模式难以持续。"
        self.assertIsNone(zh_boundary_suspect(body, "真实用量成本"))
        self.assertIsNone(zh_boundary_suspect(body, "补贴模式"))
        self.assertIsNone(zh_boundary_suspect(body, "成本"))

    def test_v3_adj_de_not_warn(self) -> None:
        """T-N10 v3:2 字形容词 + 的(`昂贵的=costly` 等)是合理 inflection,
        len==3 不再 WARN。"""
        from annotation_quality_gate import zh_boundary_suspect

        cases = [
            ("AI 真实开支变得非常昂贵的现实。", "昂贵的"),  # costly
            ("传统的月费模式已无法维系。", "传统的"),  # classical
            ("惊人的真实用量成本数字。", "惊人的"),  # astonishing
            ("数据中心的微薄的利润令人担忧。", "微薄的"),  # slender
            ("OpenAI 是其唯一的希望存在。", "唯一的"),  # sole
            ("计费逻辑发生巨大的转变出现。", "巨大的"),  # huge
            ("一个错误的优步类比说法。", "错误的"),  # erroneous (3-char,不再 WARN)
            ("数量的请求将改为按用量结算。", "数量的"),  # quantitative (3-char,放过)
        ]
        for body, anchor in cases:
            with self.subTest(anchor=anchor):
                self.assertIsNone(
                    zh_boundary_suspect(body, anchor),
                    f"v3 应不再 WARN 3 字 X+的:{anchor!r}",
                )

    def test_v3_single_char_de_still_warn(self) -> None:
        """T-N10 v3:单字 + 的(`机的`/`通的` 等)切分错位强信号,继续 WARN。"""
        from annotation_quality_gate import zh_boundary_suspect

        # 单字 + 助词,len == 2,继续 WARN
        body = "次贷危机的风险正在酝酿。"
        self.assertEqual(zh_boundary_suspect(body, "机的"), "short-zh-tail-particle")


if __name__ == "__main__":
    unittest.main()
