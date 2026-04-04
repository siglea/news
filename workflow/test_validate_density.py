#!/usr/bin/env python3
"""Tests for validate.py density heuristics (stdlib unittest)."""
from __future__ import annotations

import unittest

from validate import count_sentences_heuristic, density_warnings_for_html


def _article(body: str) -> str:
    return f'<html><article class="post-content">{body}</article></html>'


class TestCountSentencesHeuristic(unittest.TestCase):
    def test_cjk_two_clauses(self) -> None:
        self.assertEqual(count_sentences_heuristic("第一句。第二句"), 2)

    def test_cjk_one(self) -> None:
        self.assertEqual(count_sentences_heuristic("仅一句无句末标点"), 1)

    def test_english_semicolons(self) -> None:
        self.assertEqual(count_sentences_heuristic("A; B; C"), 3)

    def test_english_one(self) -> None:
        self.assertEqual(count_sentences_heuristic("Hello world."), 1)


class TestDensityWarnings(unittest.TestCase):
    def test_warns_when_blocks_below_sentences(self) -> None:
        block = (
            '<span class="word-block"><span class="english-word">a</span>'
            '<span class="word-info">[1] n.</span></span>'
        )
        # Article has at least one block globally so heuristic runs; second <p> under-dense.
        html = _article(f"<p>仅一句{block}。</p><p>第一句。第二句。</p>")
        w = density_warnings_for_html(html, "t.html")
        self.assertEqual(len(w), 1)
        self.assertIn("WARN density heuristic", w[0])
        self.assertIn("<p>#2", w[0])
        self.assertIn("~2 sentence", w[0])

    def test_no_warn_when_enough_blocks(self) -> None:
        block = (
            '<span class="word-block"><span class="english-word">a</span>'
            '<span class="word-info">[1] n.</span></span>'
        )
        html = _article(f"<p>句一{block}。句二{block}。</p>")
        w = density_warnings_for_html(html, "ok.html")
        self.assertEqual(w, [])

    def test_word_info_punct_not_counted_as_sentence_break(self) -> None:
        """Semicolon inside word-info must not inflate sentence count."""
        block = (
            '<span class="word-block"><span class="english-word">x</span>'
            '<span class="word-info">[1] v. 义甲；义乙</span></span>'
        )
        html = _article(f"<p>只有一句{block}。</p>")
        w = density_warnings_for_html(html, "x.html")
        self.assertEqual(w, [])

    def test_no_article_no_warnings(self) -> None:
        self.assertEqual(density_warnings_for_html("<p>a。b。</p>", "x"), [])

    def test_skip_when_article_has_no_word_blocks(self) -> None:
        html = _article("<p>春眠不觉晓。</p><p>处处闻啼鸟。</p>")
        self.assertEqual(density_warnings_for_html(html, "poem.html"), [])


if __name__ == "__main__":
    unittest.main()
