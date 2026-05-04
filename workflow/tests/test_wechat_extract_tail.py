"""问题 6/7: extract_wechat_plain_paragraphs 行为测试。

- 黑名单只在末尾区域生效，不误伤正文（问题 6，已合入 master）。
- 不同 source-paragraph (`<p>`/`<section>`) 的句子不应被 220 字硬合并到同一段落（问题 7）。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(ROOT / "util"))

from annotate_lib import (  # noqa: E402
    extract_wechat_plain_paragraphs,
    extract_wechat_span_leaf_paragraphs,
)


def _wrap_js_content(*paragraphs: str) -> str:
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return f'<div id="js_content">{body}</div>'


def _wrap_leaf(*sentences: str) -> str:
    """Build minimal WeChat-style HTML where each sentence is its own <span leaf>."""
    leaves = "".join(f'<section><span leaf="">{s}</span></section>' for s in sentences)
    return f'<div id="js_content">{leaves}</div>'


class TestPlainTailOnly(unittest.TestCase):
    def test_blacklist_keyword_in_body_is_kept(self) -> None:
        """正文里出现『巴伦中文网』（如转载自该媒体的稿件）必须保留。"""
        body_sentence = (
            "今年三月，巴伦中文网刊登了一篇关于美股波动的深度分析文章；"
            "我们认为其中的几个观点至今仍值得反复阅读。"
        )
        # 大量真实正文，让 body sentence 远离尾部
        filler = "正文段一段，论点充分。" * 30
        html = _wrap_js_content(filler, body_sentence, filler)
        paras = extract_wechat_plain_paragraphs(html)
        joined = "".join(paras)
        self.assertIn("巴伦中文网", joined, "body 提及『巴伦中文网』必须保留")

    def test_operational_tail_with_blacklist_is_dropped(self) -> None:
        """末尾运营句（点赞关注、成为会员、巴伦中文网公众号自我介绍等）必须丢掉。"""
        filler = "正文段一段，论点充分。" * 30
        tail = (
            "点赞关注我们的公众号。"
            "成为会员获取更多内容。"
            "本号由巴伦中文网运营，每日更新。"
        )
        html = _wrap_js_content(filler, tail)
        paras = extract_wechat_plain_paragraphs(html)
        joined = "".join(paras)
        self.assertNotIn("点赞关注", joined, "末尾『点赞关注』须被过滤")
        self.assertNotIn("成为会员", joined, "末尾『成为会员』须被过滤")

    def test_starts_with_hash_long_is_still_global_filter(self) -> None:
        """以 # 开头且长度 >30 的话题标签即使在正文中部也应被过滤（结构性硬模式）。"""
        long_tag = "#这事钛大了所以不算正文这只是一个长度超过三十字的话题标签例子。"
        body = "正文段。" * 50
        html = _wrap_js_content(body, long_tag, body)
        paras = extract_wechat_plain_paragraphs(html)
        joined = "".join(paras)
        self.assertNotIn("#这事钛大了", joined, "话题标签独立成句须过滤（不限位置）")


class TestLeafTailOnly(unittest.TestCase):
    def test_blacklist_keyword_in_body_leaf_is_kept(self) -> None:
        """span-leaf 抽取也只在末尾应用黑名单。"""
        sents = (
            ["这是正文，论述充分有力。"] * 20
            + ["巴伦中文网的某文章值得参考它的写法。"]
            + ["这是正文，论述充分有力。"] * 20
        )
        html = _wrap_leaf(*sents)
        leaves = extract_wechat_span_leaf_paragraphs(html)
        joined = "".join(leaves)
        self.assertIn(
            "巴伦中文网", joined, "leaf 模式下，body 提及『巴伦中文网』须保留"
        )

    def test_operational_tail_leaf_is_dropped(self) -> None:
        sents = (
            ["这是正文，论述充分有力。"] * 20
            + ["点赞关注我们的公众号每日更新。"]
        )
        html = _wrap_leaf(*sents)
        leaves = extract_wechat_span_leaf_paragraphs(html)
        joined = "".join(leaves)
        self.assertNotIn("点赞关注", joined, "末尾 leaf『点赞关注』须过滤")


class TestPlainParagraphBoundary(unittest.TestCase):
    """问题 7：源端 `<p>` 或 `<section>` 边界应当反映到输出段落，不应跨边界硬合并。"""

    def test_two_p_blocks_yield_separate_paragraphs(self) -> None:
        """两个 `<p>`（不同主题）→ 输出至少 2 个段落，正文文本各自独立可寻。"""
        topic_a = (
            "首段讨论的是宏观经济：今年三月联储宣布加息二十五个基点，"
            "市场提前消化，大盘窄幅波动。"
        )
        topic_b = (
            "次段切换到科技话题：英伟达发布新一代 GPU，"
            "数据中心客户的订单已经排到明年第三季度。"
        )
        html = _wrap_js_content(topic_a, topic_b)
        paras = extract_wechat_plain_paragraphs(html)
        # 至少 2 段；两个主题不应被合并到同一段
        self.assertGreaterEqual(len(paras), 2, f"应至少 2 段，实际 {len(paras)}: {paras}")
        joined_per_para = paras
        # topic_a 与 topic_b 不应同时出现在某一个段落
        for p in joined_per_para:
            both = ("联储" in p and "英伟达" in p)
            self.assertFalse(both, f"topic A 与 topic B 不应合并到同一段：{p}")

    def test_section_blocks_treated_as_paragraph_boundary(self) -> None:
        """`<section>` 也应作为段落边界，与 `<p>` 等价。"""
        html = (
            '<div id="js_content">'
            "<section>本段开篇展开宏观背景：去年开始联储进入加息周期，"
            "全球资本流动随之改变。市场分歧明显，多空双方都在等待数据出炉。</section>"
            "<section>第二段切换到结论性陈述：因此投资者应保持谨慎，"
            "等待更明确的政策信号，再做仓位变化的决定。</section>"
            "</div>"
        )
        paras = extract_wechat_plain_paragraphs(html)
        self.assertGreaterEqual(
            len(paras), 2, f"`<section>` 边界应保留，实际 {len(paras)} 段：{paras}"
        )


if __name__ == "__main__":
    unittest.main()
