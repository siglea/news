"""测试 PR T1.3: tools/ci_scope.sh 按 git diff 路由 make target。

验收点(监督/审核侧):
1. 脚本分流逻辑(util、workflow、workflow/tests → test+validate;posts/contents → validate;
   docs only → 跳过)
2. Makefile 入口一致性(`make ci-scope` 能跑通)
3. 文档可执行性(PREREQUISITES.md 命令模板可复制)

策略:在 tempdir 起一个干净 git 仓库,把 ci_scope.sh 拷过去跑,通过
让 `make` 变成"只 echo 它被传入的 target 名"的 fake 来捕获脚本决策。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent
ROOT = WORKFLOW.parent
SCRIPT = ROOT / "tools" / "ci_scope.sh"


class TestCiScope(unittest.TestCase):
    """端到端验证 ci_scope.sh 的路由决策。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mx-cisope-"))
        # 拷贝 ci_scope.sh 到 tmp/tools/
        (self.tmp / "tools").mkdir()
        shutil.copy(SCRIPT, self.tmp / "tools" / "ci_scope.sh")
        os.chmod(self.tmp / "tools" / "ci_scope.sh", 0o755)

        # 写一个 fake make 脚本捕获 target 名
        fake_make_dir = self.tmp / "fake-bin"
        fake_make_dir.mkdir()
        fake_make = fake_make_dir / "make"
        fake_make.write_text(
            '#!/usr/bin/env bash\n'
            'echo "MAKE_TARGET:$@" >> "$CI_SCOPE_TEST_LOG"\n'
            'exit 0\n'
        )
        os.chmod(fake_make, 0o755)
        self.fake_bin = fake_make_dir
        self.log_path = self.tmp / "captured.log"

        # 起 git 仓库
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(["git", "config", "user.email", "t@x"], cwd=self.tmp, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=self.tmp, check=True)
        # 初始 commit (空)
        (self.tmp / "README.md").write_text("seed\n")
        subprocess.run(["git", "add", "."], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "seed"], cwd=self.tmp, check=True
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_scope(self, *, staged: bool = True) -> tuple[str, int]:
        """跑 ci_scope.sh,返回 captured make 调用 + 退出码。"""
        env = os.environ.copy()
        env["PATH"] = f"{self.fake_bin}:{env['PATH']}"
        env["CI_SCOPE_TEST_LOG"] = str(self.log_path)
        args = ["bash", "tools/ci_scope.sh"]
        if staged:
            args.append("--staged")
        cp = subprocess.run(
            args, cwd=self.tmp, env=env, capture_output=True, text=True
        )
        log = self.log_path.read_text() if self.log_path.exists() else ""
        return log, cp.returncode

    def _stage(self, path: str, content: str = "x\n") -> None:
        full = self.tmp / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        subprocess.run(["git", "add", path], cwd=self.tmp, check=True)

    # ---- 路由测试 ----

    def test_python_source_change_runs_test_and_validate(self) -> None:
        """workflow/*.py 改动应触发 test + validate。"""
        self._stage("workflow/foo.py", "print('hi')\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0, f"非零退出码:{log}")
        self.assertIn("MAKE_TARGET:test", log, f"应跑 make test,实际:\n{log}")
        self.assertIn("MAKE_TARGET:validate", log)

    def test_workflow_tests_change_runs_test_and_validate(self) -> None:
        """workflow/tests/*.py 改动应触发 test + validate。"""
        self._stage("workflow/tests/test_foo_unit.py", "import unittest\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0, f"非零退出码:{log}")
        self.assertIn("MAKE_TARGET:test", log, f"应跑 make test,实际:\n{log}")
        self.assertIn("MAKE_TARGET:validate", log)

    def test_util_source_change_runs_test_and_validate(self) -> None:
        self._stage("util/bar.py", "x=1\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0)
        self.assertIn("MAKE_TARGET:test", log)
        self.assertIn("MAKE_TARGET:validate", log)

    def test_posts_only_change_runs_validate_no_test(self) -> None:
        """改 posts/ 只跑 validate。"""
        self._stage("posts/2026-04-30-foo.html", "<html></html>\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0)
        self.assertNotIn("MAKE_TARGET:test", log, f"posts-only 不应跑 make test:\n{log}")
        self.assertIn("MAKE_TARGET:validate", log)

    def test_index_html_change_runs_validate(self) -> None:
        self._stage("index.html", "<html></html>\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0)
        self.assertIn("MAKE_TARGET:validate", log)
        self.assertNotIn("MAKE_TARGET:test", log)

    def test_drafts_change_runs_validate(self) -> None:
        self._stage("content/drafts/foo/meta.json", "{}\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0)
        self.assertIn("MAKE_TARGET:validate", log)

    def test_docs_only_change_skips_ci(self) -> None:
        """仅 docs 改动应跳过 CI(无 make 调用)。"""
        self._stage("docs/whatever.md", "## hi\n")
        self._stage("README.md", "seed2\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0, f"docs-only 应 exit 0:\n{log}")
        self.assertNotIn(
            "MAKE_TARGET:", log,
            f"仅 docs 改动不应触发任何 make 调用,实际:\n{log}",
        )

    def test_makefile_change_runs_validate(self) -> None:
        """Makefile 自身改动应触发 validate(配置兜底)。"""
        self._stage("Makefile", "x:\n\techo hi\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0)
        self.assertIn("MAKE_TARGET:validate", log)

    def test_unknown_file_falls_back_to_validate(self) -> None:
        """未知路径默认跑 validate(保守兜底)。"""
        self._stage(".gitignore", "*.tmp\n")
        log, rc = self._run_scope()
        self.assertEqual(rc, 0)
        self.assertIn("MAKE_TARGET:validate", log)


if __name__ == "__main__":
    unittest.main()
