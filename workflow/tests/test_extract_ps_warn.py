"""问题 8: extract_ps 丢弃 ≤10 字 `<p>` 时,默认在 stderr 给出诊断。

行为契约:
- 默认参数 `warn=True`:有短段被丢时,emit `[extract_ps] dropped N ...` 到 stderr。
- `warn=False`:完全静默(供批量脚本使用)。
- 抽出来的段落数与历史一致(行为相同,只是多了诊断信号)。
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(ROOT / "util"))

from annotate_lib import extract_ps  # noqa: E402


SHORT_HTML = (
    "<html><body>"
    "<p>标题</p>"  # len=2,要被丢
    "<p>关注我们</p>"  # len=4,要被丢
    "<p>这是一段足够长的正文内容，应该被保留下来。</p>"  # 21 字,保留
    "<p>另一段更长的正文，里面有些细节可以被读者反复阅读。</p>"  # 24 字,保留
    "<p>—</p>"  # len=1,要被丢
    "</body></html>"
)


class TestExtractPsWarn(unittest.TestCase):
    def test_warn_emits_diagnostic_to_stderr(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            paras = extract_ps(SHORT_HTML)  # default warn=True
        msg = buf.getvalue()
        self.assertIn("[extract_ps] dropped", msg, "应输出诊断 prefix")
        self.assertIn("samples:", msg, "应包含 samples 字段")
        # 诊断里应该至少含一个被丢的样本
        self.assertTrue(
            any(s in msg for s in ("'标题'", "'关注我们'", "'—'")),
            f"samples 应含被丢字符串之一，实际:{msg}",
        )
        # 段落数应当与原行为一致(只保留长段)
        self.assertEqual(len(paras), 2)

    def test_warn_false_is_silent(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            paras = extract_ps(SHORT_HTML, warn=False)
        self.assertEqual(buf.getvalue(), "", "warn=False 必须完全静默")
        self.assertEqual(len(paras), 2)

    def test_no_drop_no_warn(self) -> None:
        """没有被丢的短段时,即便 warn=True 也不应输出。"""
        clean = (
            "<html><body>"
            "<p>第一段较长正文，足够过 10 字门槛。</p>"
            "<p>第二段同样较长，过门槛。</p>"
            "</body></html>"
        )
        buf = io.StringIO()
        with redirect_stderr(buf):
            paras = extract_ps(clean)
        self.assertEqual(buf.getvalue(), "", "无丢弃时 stderr 应静默")
        self.assertEqual(len(paras), 2)


if __name__ == "__main__":
    unittest.main()
