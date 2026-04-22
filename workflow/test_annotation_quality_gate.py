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

if __name__ == "__main__":
    unittest.main()
