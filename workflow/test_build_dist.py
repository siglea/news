"""问题 2(B): tools/build_dist.sh 只把白名单文件放进 ./dist，不外露内部目录。"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent
ROOT = WORKFLOW.parent
DIST = ROOT / "dist"
SCRIPT = ROOT / "tools" / "build_dist.sh"


class TestBuildDist(unittest.TestCase):
    """运行 tools/build_dist.sh,验证 dist/ 含且仅含外网应见的资源。"""

    @classmethod
    def setUpClass(cls) -> None:
        if DIST.exists():
            shutil.rmtree(DIST)
        cp = subprocess.run(
            ["bash", str(SCRIPT)], cwd=str(ROOT), capture_output=True, text=True
        )
        if cp.returncode != 0:
            raise RuntimeError(
                f"build_dist.sh failed: rc={cp.returncode}\n"
                f"stdout: {cp.stdout}\nstderr: {cp.stderr}"
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if DIST.exists():
            shutil.rmtree(DIST)

    def test_public_files_present(self) -> None:
        for name in ("index.html", "about.html", "favicon.ico"):
            self.assertTrue(
                (DIST / name).is_file(), f"dist/{name} 应存在"
            )

    def test_public_dirs_present(self) -> None:
        for d in ("posts", "css", "js", "images"):
            self.assertTrue(
                (DIST / d).is_dir(), f"dist/{d}/ 应存在"
            )

    def test_internal_dirs_not_present(self) -> None:
        """内部源码、草稿、文档等绝不能进入 dist/。"""
        for d in (
            "content", "workflow", "util", "docs", "tools", ".edgeone", ".git"
        ):
            self.assertFalse(
                (DIST / d).exists(), f"dist/{d} 不应存在(内部资源不可外露)"
            )

    def test_internal_files_not_present(self) -> None:
        for f in (
            "Makefile", ".coze", ".gitignore", "README.md", "edgeone.json",
            "_config.yml", "LICENSE",
        ):
            self.assertFalse(
                (DIST / f).exists(), f"dist/{f} 不应存在"
            )

    def test_posts_count_matches_repo(self) -> None:
        """dist/posts/ 与仓库 posts/ 文件数应一致(整目录拷贝)。"""
        repo_posts = sorted(p.name for p in (ROOT / "posts").glob("*.html"))
        dist_posts = sorted(p.name for p in (DIST / "posts").glob("*.html"))
        self.assertEqual(repo_posts, dist_posts)


if __name__ == "__main__":
    unittest.main()
