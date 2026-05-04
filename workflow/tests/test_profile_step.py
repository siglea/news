"""测试 PR T2.1: workflow/mingox.py 的 _profile_step 上下文管理器。

行为契约:
- 默认 `MX_PROFILE` 未设 → 完全静默(无 stderr 输出)
- `MX_PROFILE=1` / `true` / `yes` / `on` / `stderr` → 输出 `[profile] step=<name> dur_ms=<n> rc=<code>`
- 步骤抛 SystemExit → rc 标签反映 exit code
- 步骤抛其它异常 → rc=raised
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKFLOW))

from mingox import _profile_enabled, _profile_step  # noqa: E402


class TestProfileEnabled(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.get("MX_PROFILE", None)
        os.environ.pop("MX_PROFILE", None)

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("MX_PROFILE", None)
        else:
            os.environ["MX_PROFILE"] = self._saved

    def test_default_off(self) -> None:
        self.assertFalse(_profile_enabled())

    def test_truthy_values(self) -> None:
        for v in ("1", "true", "yes", "on", "stderr", "TRUE", "Yes"):
            os.environ["MX_PROFILE"] = v
            with self.subTest(MX_PROFILE=v):
                self.assertTrue(_profile_enabled(), f"{v!r} 应被识别为 enabled")

    def test_falsy_values(self) -> None:
        for v in ("", "0", "false", "no", "off", "random"):
            os.environ["MX_PROFILE"] = v
            with self.subTest(MX_PROFILE=v):
                self.assertFalse(_profile_enabled())


class TestProfileStep(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.get("MX_PROFILE", None)

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("MX_PROFILE", None)
        else:
            os.environ["MX_PROFILE"] = self._saved

    def test_silent_when_off(self) -> None:
        os.environ.pop("MX_PROFILE", None)
        buf = io.StringIO()
        with redirect_stderr(buf):
            with _profile_step("foo"):
                pass
        self.assertEqual(buf.getvalue(), "")

    def test_emits_when_on(self) -> None:
        os.environ["MX_PROFILE"] = "1"
        buf = io.StringIO()
        with redirect_stderr(buf):
            with _profile_step("foo"):
                pass
        out = buf.getvalue()
        self.assertIn("[profile]", out)
        self.assertIn("step=foo", out)
        self.assertIn("dur_ms=", out)
        self.assertIn("rc=0", out)

    def test_systemexit_records_code(self) -> None:
        os.environ["MX_PROFILE"] = "1"
        buf = io.StringIO()
        with redirect_stderr(buf):
            with self.assertRaises(SystemExit):
                with _profile_step("oops"):
                    raise SystemExit(7)
        out = buf.getvalue()
        self.assertIn("step=oops", out)
        self.assertIn("rc=7", out)

    def test_other_exception_records_raised(self) -> None:
        os.environ["MX_PROFILE"] = "1"
        buf = io.StringIO()
        with redirect_stderr(buf):
            with self.assertRaises(ValueError):
                with _profile_step("boom"):
                    raise ValueError("nope")
        out = buf.getvalue()
        self.assertIn("step=boom", out)
        self.assertIn("rc=raised", out)

    def test_dur_ms_is_nonnegative_integer(self) -> None:
        os.environ["MX_PROFILE"] = "1"
        buf = io.StringIO()
        with redirect_stderr(buf):
            with _profile_step("quick"):
                pass
        # 解析 dur_ms 数字
        line = buf.getvalue().strip()
        # 形如 [profile] step=quick dur_ms=0 rc=0
        parts = dict(seg.split("=") for seg in line.split() if "=" in seg)
        self.assertIn("dur_ms", parts)
        self.assertGreaterEqual(int(parts["dur_ms"]), 0)


if __name__ == "__main__":
    unittest.main()
