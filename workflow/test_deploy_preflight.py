"""测试 PR T2.4: cmd_deploy 前置 fail-fast 检查。

行为契约:
- npx 不在 PATH → SystemExit(2)
- build_dist.sh 不存在 → SystemExit(2)
- 公开资源(index.html / posts/)缺失 → SystemExit(2)
- token 文件存在且非空 → auth='file', has_explicit=True
- 仅 EDGEONE_API_TOKEN env var → auth='env', has_explicit=True
- 都没有 → auth='cli-cached', has_explicit=False(WARN 但不 fail)
- token 文件为空 → 等价于"无 token",emit WARN
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

WORKFLOW = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKFLOW))

import mingox  # noqa: E402


class TestPreflight(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mx-preflight-"))
        # 模拟一个最小可通过的 repo:index.html + posts/ + tools/build_dist.sh
        (self.tmp / "index.html").write_text("<html></html>")
        (self.tmp / "posts").mkdir()
        (self.tmp / "tools").mkdir()
        (self.tmp / "tools" / "build_dist.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
        (self.tmp / ".edgeone").mkdir()
        # patch ROOT so preflight 用 tmp 目录
        self._patch_root = mock.patch.object(mingox, "ROOT", self.tmp)
        self._patch_root.start()
        # 保存并清理 EDGEONE_API_TOKEN
        self._saved_env = os.environ.get("EDGEONE_API_TOKEN", None)
        os.environ.pop("EDGEONE_API_TOKEN", None)

    def tearDown(self) -> None:
        self._patch_root.stop()
        if self._saved_env is None:
            os.environ.pop("EDGEONE_API_TOKEN", None)
        else:
            os.environ["EDGEONE_API_TOKEN"] = self._saved_env
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, **kwargs):
        token_path = kwargs.get("token_path", self.tmp / ".edgeone" / ".token")
        build_script = kwargs.get("build_script", self.tmp / "tools" / "build_dist.sh")
        return mingox._deploy_preflight(token_path, build_script)

    def test_token_file_detected(self) -> None:
        (self.tmp / ".edgeone" / ".token").write_text("abc123")
        auth, has_explicit = self._run()
        self.assertEqual(auth, "file")
        self.assertTrue(has_explicit)

    def test_env_token_fallback(self) -> None:
        os.environ["EDGEONE_API_TOKEN"] = "env-token"
        auth, has_explicit = self._run()
        self.assertEqual(auth, "env")
        self.assertTrue(has_explicit)

    def test_no_auth_warns_not_fails(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            auth, has_explicit = self._run()
        self.assertEqual(auth, "cli-cached")
        self.assertFalse(has_explicit)
        self.assertIn("未发现", buf.getvalue())

    def test_empty_token_file_warns(self) -> None:
        (self.tmp / ".edgeone" / ".token").write_text("   \n")  # only whitespace
        buf = io.StringIO()
        with redirect_stderr(buf):
            auth, has_explicit = self._run()
        self.assertEqual(auth, "cli-cached")
        self.assertIn("为空", buf.getvalue())

    def test_missing_index_html_fails(self) -> None:
        (self.tmp / "index.html").unlink()
        with self.assertRaises(SystemExit) as cm:
            self._run()
        self.assertEqual(cm.exception.code, 2)

    def test_missing_posts_dir_fails(self) -> None:
        shutil.rmtree(self.tmp / "posts")
        with self.assertRaises(SystemExit) as cm:
            self._run()
        self.assertEqual(cm.exception.code, 2)

    def test_missing_build_script_fails(self) -> None:
        (self.tmp / "tools" / "build_dist.sh").unlink()
        with self.assertRaises(SystemExit) as cm:
            self._run()
        self.assertEqual(cm.exception.code, 2)

    def test_missing_npx_fails(self) -> None:
        # patch shutil.which to None
        with mock.patch("mingox.shutil.which", return_value=None):
            with self.assertRaises(SystemExit) as cm:
                self._run()
            self.assertEqual(cm.exception.code, 2)

    def test_emits_ok_line_with_auth(self) -> None:
        (self.tmp / ".edgeone" / ".token").write_text("abc")
        buf = io.StringIO()
        with redirect_stderr(buf):
            self._run()
        self.assertIn("[deploy preflight] OK auth=file", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
