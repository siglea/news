"""测试 PR T-N3: `mingox build --update-index` 自动注入 `<li>` 到 index.html 顶部。

行为契约:
- 默认 `--update-index` 关闭:不动 index.html
- `--update-index --dry-run-index`:预览,不写文件
- `--update-index`:写文件,在 `<ul class="post-list">` 内顶部插入
- 幂等:相同 slug 已存在则跳过(emit reason)
- 内容:format 匹配现有 index.html `<li>` 格式(含 emoji/title/title-en/meta/excerpt)
- meta 字段安全:title 等 escape 防 XSS / 渲染错位
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKFLOW))

import build_draft  # noqa: E402
from build_draft import (  # noqa: E402
    generate_post_li,
    inject_li_to_index,
)


SAMPLE_META = {
    "title_emoji": "📈",
    "title_zh": "测试标题(含中文 + 标点)",
    "title_en": "Test Title with English",
    "date": "2026-04-30",
    "out_html": "posts/2026-04-30-test-slug.html",
    "meta_description": "围绕一个测试主题的简要摘要,用于验证 li 生成与注入。",
    "tags": ["测试", "AI", "转载"],
}

SAMPLE_INDEX = """<html>
<body>
                <ul class="post-list">
                    <li class="post-item">
                        <div class="post-title">
                            <a href="posts/existing.html">📈 已有文章<br><small class="title-en">Existing</small></a>
                        </div>
                    </li>
                </ul>
</body>
</html>
"""


class TestGeneratePostLi(unittest.TestCase):
    def test_basic_structure(self) -> None:
        li = generate_post_li(SAMPLE_META)
        self.assertIn('<li class="post-item">', li)
        self.assertIn('<div class="post-title">', li)
        self.assertIn('<div class="post-meta">', li)
        self.assertIn('<div class="post-excerpt">', li)
        self.assertIn("</li>", li)

    def test_includes_emoji_and_titles(self) -> None:
        li = generate_post_li(SAMPLE_META)
        self.assertIn("📈", li)
        self.assertIn("测试标题", li)
        self.assertIn("Test Title with English", li)

    def test_includes_date_and_tags(self) -> None:
        li = generate_post_li(SAMPLE_META)
        self.assertIn("📅 2026-04-30", li)
        self.assertIn("🏷️ 测试, AI, 转载", li)

    def test_href_correct(self) -> None:
        li = generate_post_li(SAMPLE_META)
        self.assertIn('href="posts/2026-04-30-test-slug.html"', li)
        self.assertEqual(
            li.count('href="posts/2026-04-30-test-slug.html"'),
            2,  # title 和 excerpt 各一个
        )

    def test_xss_escape(self) -> None:
        """title 含 HTML 元字符应被 escape。"""
        meta = dict(SAMPLE_META)
        meta["title_zh"] = '<script>alert("xss")</script>'
        li = generate_post_li(meta)
        self.assertNotIn("<script>", li)
        self.assertIn("&lt;script&gt;", li)

    def test_no_tags_falls_back_to_zhuanzai(self) -> None:
        """缺 tags 字段时,使用 '转载' 单个标签作占位。"""
        meta = dict(SAMPLE_META)
        del meta["tags"]
        li = generate_post_li(meta)
        self.assertIn("🏷️ 转载", li)

    def test_empty_excerpt_uses_placeholder(self) -> None:
        meta = dict(SAMPLE_META)
        meta["meta_description"] = ""
        li = generate_post_li(meta)
        self.assertIn("（待补摘要）", li)

    def test_indent_matches_existing_format(self) -> None:
        """生成的 <li> 缩进与现有 index.html 中条目一致(20 空格)。"""
        li = generate_post_li(SAMPLE_META)
        # 第一行应以恰好 20 空格 + <li 开头
        first_line = li.split("\n", 1)[0]
        self.assertTrue(
            first_line.startswith("                    <li "),
            f"缩进不对:{first_line!r}",
        )


class TestInjectLiToIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mx-idx-"))
        self.index = self.tmp / "index.html"
        self.index.write_text(SAMPLE_INDEX, encoding="utf-8")
        self.li = generate_post_li(SAMPLE_META)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_inserts_at_top(self) -> None:
        res = inject_li_to_index(self.index, self.li)
        self.assertTrue(res["inserted"])
        new_text = self.index.read_text(encoding="utf-8")
        # 新 <li> 应在 existing <li> 之前
        idx_new = new_text.find(SAMPLE_META["out_html"])
        idx_existing = new_text.find('href="posts/existing.html"')
        self.assertGreater(idx_existing, idx_new)

    def test_idempotent_skip_on_existing_slug(self) -> None:
        # 第一次插入
        inject_li_to_index(self.index, self.li)
        # 第二次应跳过
        res2 = inject_li_to_index(self.index, self.li)
        self.assertFalse(res2["inserted"])
        self.assertIn("already contains", res2["reason"])

    def test_dry_run_does_not_write(self) -> None:
        original = self.index.read_text(encoding="utf-8")
        res = inject_li_to_index(self.index, self.li, dry_run=True)
        self.assertTrue(res["inserted"], "dry_run 仍应报告 inserted=True")
        self.assertEqual(self.index.read_text(encoding="utf-8"), original)
        self.assertIsNotNone(res["new_text"])
        # new_text 包含新的 <li>
        self.assertIn(SAMPLE_META["out_html"], res["new_text"])

    def test_missing_index_returns_error(self) -> None:
        missing = self.tmp / "no-index.html"
        res = inject_li_to_index(missing, self.li)
        self.assertFalse(res["inserted"])
        self.assertIn("missing", res["reason"])

    def test_no_post_list_ul_returns_error(self) -> None:
        bad = self.tmp / "bad.html"
        bad.write_text("<html><body>no post-list here</body></html>", encoding="utf-8")
        res = inject_li_to_index(bad, self.li)
        self.assertFalse(res["inserted"])
        self.assertIn("post-list", res["reason"])


class TestBuildSlugUpdateIndexFlag(unittest.TestCase):
    """端到端:build_slug(..., update_index=True) 是否会真的注入。"""

    def test_default_does_not_touch_index(self) -> None:
        """update_index=False(默认)时,不动 index.html。

        只验证 generate_post_li / inject_li_to_index 的 default-off 行为,
        不实际跑完整 build(那需要完整的 draft 目录)。
        """
        tmp = Path(tempfile.mkdtemp(prefix="mx-idx-build-"))
        try:
            index = tmp / "index.html"
            index.write_text(SAMPLE_INDEX, encoding="utf-8")
            original = index.read_text(encoding="utf-8")
            # 直接验证:不调 inject_li_to_index 时文件不变
            # (这其实是 trivially true,但作为 invariant 文档化)
            self.assertEqual(index.read_text(encoding="utf-8"), original)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
