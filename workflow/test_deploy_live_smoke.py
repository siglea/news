"""测试 T-N7: deploy 后自动线上抽检。"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

WORKFLOW = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKFLOW))

import mingox  # noqa: E402


class TestPreviewUrlForPath(unittest.TestCase):
    def test_keep_query_token(self) -> None:
        preview = "https://example.cool?eo_token=abc&eo_time=1"
        u = mingox._preview_url_for_path(preview, "/posts/a.html")
        self.assertEqual(
            u,
            "https://example.cool/posts/a.html?eo_token=abc&eo_time=1",
        )


class TestDeployLiveSmoke(unittest.TestCase):
    def test_warn_on_status_mismatch(self) -> None:
        preview = "https://example.cool?eo_token=abc"
        # post=200, util=404, drafts=404 才是通过；这里故意让 util=200 触发告警
        status_map = {
            "https://example.cool/posts/x.html?eo_token=abc": 200,
            "https://example.cool/util/annotate_lib.py?eo_token=abc": 200,
            "https://example.cool/content/drafts/?eo_token=abc": 404,
        }

        def fake_http_status(url: str, timeout_sec: float = 15.0) -> int:
            return status_map[url]

        buf = io.StringIO()
        with mock.patch("mingox._http_status", side_effect=fake_http_status), redirect_stderr(buf):
            mingox._deploy_live_smoke_check(preview, post_path="posts/x.html")
        self.assertIn("[deploy smoke] WARN:", buf.getvalue())
        self.assertIn("internal-util", buf.getvalue())

    def test_ok_when_all_expected(self) -> None:
        preview = "https://example.cool?eo_token=abc"
        status_map = {
            "https://example.cool/index.html?eo_token=abc": 200,
            "https://example.cool/util/annotate_lib.py?eo_token=abc": 404,
            "https://example.cool/content/drafts/?eo_token=abc": 404,
        }

        def fake_http_status(url: str, timeout_sec: float = 15.0) -> int:
            return status_map[url]

        buf = io.StringIO()
        with mock.patch("mingox._http_status", side_effect=fake_http_status), redirect_stderr(buf):
            mingox._deploy_live_smoke_check(preview, post_path=None)
        self.assertIn("[deploy smoke] OK:", buf.getvalue())


class TestHttpStatusFallback(unittest.TestCase):
    def test_urlerror_returns_negative_one(self) -> None:
        with mock.patch("mingox.urlrequest.urlopen", side_effect=mingox.urlerror.URLError("dns")):
            self.assertEqual(mingox._http_status("https://example.test"), -1)


class TestCloseLoopDeployPassesPostPath(unittest.TestCase):
    def test_close_loop_deploy_includes_post_check(self) -> None:
        # 用 mock 拦截 _run_step 检查 deploy 子命令
        tmp = Path("/tmp/non-existent-for-test")
        with mock.patch("mingox.ROOT", tmp):
            pass

        # 构造最小工作目录
        import tempfile
        import json

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            draft = root / "content" / "drafts" / "s"
            draft.mkdir(parents=True)
            (draft / "01-source.md").write_text("x", encoding="utf-8")
            (draft / "llm_annotations.json").write_text("{}", encoding="utf-8")
            (draft / "meta.json").write_text(json.dumps({"out_html": "posts/2026-04-30-s.html"}), encoding="utf-8")
            captured: list[list[str]] = []

            def fake_run_step(cmd: list[str]) -> int:
                captured.append(cmd)
                return 0

            with mock.patch("mingox.ROOT", root), mock.patch("mingox._run_step", side_effect=fake_run_step):
                args = type("Args", (), {"slug": "s", "deploy": True, "project": "mingox"})
                mingox.cmd_close_loop(args)

            deploy_cmd = [c for c in captured if len(c) > 2 and c[2] == "deploy"][0]
            self.assertIn("--post-check", deploy_cmd)
            self.assertIn("posts/2026-04-30-s.html", deploy_cmd)


if __name__ == "__main__":
    unittest.main()

