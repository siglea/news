"""测试 PR-B: `close-loop` 在 build 前先跑 `validate --annotations` 作为 fail-fast gate。

验收点(监督/审核侧):
1. annotations-gate 在 build 之前执行(顺序正确)
2. 不影响现有 close-loop 正常路径(default 行为兼容)
3. 失败前移场景:annotations-gate 失败应阻断 build
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

WORKFLOW = Path(__file__).resolve().parent
ROOT = WORKFLOW.parent
sys.path.insert(0, str(WORKFLOW))


class TestCloseLoopAnnotationsGate(unittest.TestCase):
    """验证 close-loop 步骤数组的顺序与命令拼装。

    用 mock 拦截 `_run_step`,捕获每步的命令以便断言;不实际跑 build/deploy。
    """

    def _make_minimal_draft(self, root: Path, slug: str) -> None:
        draft = root / "content" / "drafts" / slug
        draft.mkdir(parents=True)
        # 最小 meta + source + annotations 让 cmd_close_loop 能进入 steps 数组
        (draft / "meta.json").write_text(
            json.dumps({"out_html": f"posts/2026-04-30-{slug}.html"}),
            encoding="utf-8",
        )
        (draft / "01-source.md").write_text("dummy", encoding="utf-8")
        (draft / "llm_annotations.json").write_text("{}", encoding="utf-8")

    def test_step_order_annotations_gate_before_build(self) -> None:
        """断言 close-loop 先跑 annotations-gate,再跑 build,再跑 validate。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            slug = "fixture-slug"
            self._make_minimal_draft(tmp_root, slug)

            # 把 ROOT patch 到 tmp,这样 cmd_close_loop 找的 draft 是 fixture
            captured: list[tuple[str, list[str]]] = []

            def fake_run_step(cmd: list[str]) -> int:
                # 解析 step 名:cmd 形如 [py, wf, "annotations-gate"|"build"|"validate"|"deploy", ...]
                # 但 close-loop 内部 step name 是元组里的 name,不在 cmd 里
                # 直接捕获 cmd 即可,然后从 cmd[2] 推断 subcommand
                subcmd = cmd[2] if len(cmd) > 2 else "?"
                captured.append((subcmd, cmd))
                return 0  # 总是成功,让所有步骤都执行

            with mock.patch("mingox.ROOT", tmp_root), \
                 mock.patch("mingox._run_step", side_effect=fake_run_step):
                import mingox

                args = argparse.Namespace(
                    slug=slug, deploy=False, project="mingox"
                )
                try:
                    mingox.cmd_close_loop(args)
                except SystemExit as e:
                    # 正常 close-loop 不 SystemExit;若发生说明 step 失败
                    self.fail(f"close-loop unexpectedly exited: {e}")

            # 提取 subcommand 顺序
            order = [c[0] for c in captured]
            self.assertEqual(
                order, ["validate", "build", "validate"],
                f"步骤顺序应为 validate(annotations-gate) → build → validate(post),实际:{order}",
            )

            # 第一步应该是 annotations gate(`validate --annotations`)
            first_cmd = captured[0][1]
            self.assertIn("--annotations", first_cmd, "第一步必须是 annotations gate")
            self.assertIn("--slug", first_cmd, "annotations gate 应针对单个 slug")

            # 第二步是 build
            self.assertEqual(captured[1][0], "build")

            # 第三步是 post validate
            self.assertIn("--post", captured[2][1])

    def test_annotations_gate_failure_blocks_build(self) -> None:
        """如果 annotations-gate 失败,build 不应被调用 → fail-fast 实现正确。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            slug = "fixture-fail"
            self._make_minimal_draft(tmp_root, slug)

            captured: list[tuple[str, list[str]]] = []

            def fake_run_step(cmd: list[str]) -> int:
                subcmd = cmd[2] if len(cmd) > 2 else "?"
                captured.append((subcmd, cmd))
                # 第一步 annotations-gate 故意 fail
                if "--annotations" in cmd:
                    return 1
                return 0

            with mock.patch("mingox.ROOT", tmp_root), \
                 mock.patch("mingox._run_step", side_effect=fake_run_step):
                import mingox

                args = argparse.Namespace(
                    slug=slug, deploy=False, project="mingox"
                )
                with self.assertRaises(SystemExit) as cm:
                    mingox.cmd_close_loop(args)
                self.assertEqual(cm.exception.code, 1)

            # 应该只跑了 annotations-gate(因为失败后立即 raise SystemExit)
            self.assertEqual(
                len(captured), 1,
                f"annotations-gate 失败时不应跑 build/validate,实际跑了:{[c[0] for c in captured]}",
            )
            self.assertIn("--annotations", captured[0][1])


if __name__ == "__main__":
    unittest.main()
