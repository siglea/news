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
        from annotation_quality_gate import zh_boundary_suspect

        body1 = "一场类似次贷危机的风险正在酝酿。"
        body2 = "固定数量的请求将改为按用量结算。"
        self.assertEqual(zh_boundary_suspect(body1, "机的"), "short-zh-tail-particle")
        self.assertEqual(zh_boundary_suspect(body2, "数量的"), "short-zh-tail-particle")

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

if __name__ == "__main__":
    unittest.main()
