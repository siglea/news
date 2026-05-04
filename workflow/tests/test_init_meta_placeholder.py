"""测试 PR-A: `init` 写入 `meta_description` 占位符,build quality gate 不会 fail。

验收点(监督/审核侧):
1. 占位符稳定通过现有 quality gate(`meta_description` non-empty)
2. 占位符明显含「[占位」前缀,acquire/编辑后不会漏改
3. 不依赖任何外部 LLM 或 API key(harness/环境无关)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(WORKFLOW))
sys.path.insert(0, str(ROOT / "util"))

from acquire import _default_meta_description_placeholder  # noqa: E402
from annotation_quality_gate import check_quality  # noqa: E402


class TestPlaceholder(unittest.TestCase):
    def test_non_empty(self) -> None:
        s = _default_meta_description_placeholder("测试标题")
        self.assertTrue(len(s) > 0, "占位符不能为空")

    def test_contains_marker(self) -> None:
        """占位符须含明显「[占位」标记,提醒人/agent 后续替换。"""
        s = _default_meta_description_placeholder("某文章标题")
        self.assertIn("[占位", s, "占位符须含明显标记")

    def test_includes_title(self) -> None:
        title = "巴菲特预警美股崩盘的关键指标"
        s = _default_meta_description_placeholder(title)
        self.assertIn(title, s, "占位符应包含 title_zh,提供基础上下文")

    def test_handles_empty_title(self) -> None:
        s = _default_meta_description_placeholder("")
        self.assertTrue(len(s) > 0, "title_zh 为空时仍返回非空字符串")
        self.assertIn("未填写", s, "应明确指出 title_zh 缺失")

    def test_handles_none_title(self) -> None:
        # type: ignore — 测试鲁棒性
        s = _default_meta_description_placeholder(None)  # type: ignore[arg-type]
        self.assertTrue(len(s) > 0)

    def test_passes_quality_gate(self) -> None:
        """使用占位符的 meta + 最小 annotations payload 不会触发 quality gate FAIL。"""
        meta = {
            "meta_description": _default_meta_description_placeholder("某稿"),
        }
        # 一个最小可通过的 annotations payload(空标注列表也应允许 non-empty meta_desc)
        payload = {"version": 1, "annotations": []}
        errors, _warnings = check_quality(meta, payload)
        # quality_gate 对 meta_description 唯一要求是 non-empty
        # 不应因占位符而 FAIL
        for e in errors:
            self.assertNotIn(
                "meta_description", e,
                f"quality_gate 不应因占位符 meta_description 报错,实际:{e}",
            )

    def test_no_external_dep(self) -> None:
        """函数实现应纯本地拼字符串,不调用任何 socket/http。

        (这不是真正的 sandbox 测试,但确保函数体里没引入外部 import)
        """
        import inspect
        from acquire import _default_meta_description_placeholder as fn

        src = inspect.getsource(fn)
        for forbidden in ("urllib", "requests", "anthropic", "openai", "http.client", "socket"):
            self.assertNotIn(forbidden, src, f"占位符函数不应引入 {forbidden}")


if __name__ == "__main__":
    unittest.main()
