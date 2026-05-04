"""测试 PR T-N2: `mingox normalize-source` 检测/截断 01-source.md 末尾运营段。

验收点(监督/审核侧):
1. **误伤率**:正文中部出现"扫码"/"关注"等不应触发截断
2. **默认 --check 零破坏**:文件不被修改
3. **--auto-truncate 触发条件可解释**:仅在尾部 high-conf 命中时实际截断
4. **单测覆盖反例**:运营词出现在正文中部不应触发

T-N9 扩展(2026-04-30):补全公众号经典尾巴 pattern
- "在看"系(`觉得好看,请点"在看"` 是 ai-subprime 上线漏抓的 must-fix 复现)
- 三连系(`点赞收藏` / `点赞、转发` / `点赞、在看`)
- 星标系(`加为星标` / `设为星标` / `星标我们`)
- 朋友圈系(`转发朋友圈` / `分享朋友圈`)
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

WORKFLOW = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKFLOW))

import mingox  # noqa: E402
from mingox import (  # noqa: E402
    _CROSS_PROMO_RE,
    _find_truncation_point,
    _is_body_paragraph,
    _is_operational_paragraph,
)


class TestPatternMatching(unittest.TestCase):
    """单元层:运营 pattern 识别函数。"""

    def test_high_conf_keywords(self) -> None:
        for kw in (
            "扫描二维码添加小助手微信",
            "请关注公众号「机器学习」",
            "点击阅读原文了解更多",
            "成为会员,获取深度内容",
            "诚邀各领域优秀企业参与申报",
        ):
            with self.subTest(kw=kw):
                is_op, label = _is_operational_paragraph(kw)
                self.assertTrue(is_op, f"{kw!r} 应被识别为 high-conf 运营段")
                self.assertTrue(label.startswith("high-conf"), label)

    def test_body_text_with_passing_keyword_not_op(self) -> None:
        """正文中提到 '关注' 等词不应被误判为运营段(因有 high-conf 阈值)。"""
        body_with_keyword = (
            "本文重点关注美股估值的回归路径,具体细节见下文。"
            "我们将讨论巴菲特指标的历史表现以及当前 232% 的极端读数。"
        )
        is_op, label = _is_operational_paragraph(body_with_keyword)
        # "关注" 是单字,不在 high-conf 列表("关注公众号"才是)
        self.assertFalse(is_op, f"误判:{label}")

    def test_cross_promo_detected(self) -> None:
        s = "起底游戏周边 | 白银之城 | 离职字节创业"
        is_op, label = _is_operational_paragraph(s)
        self.assertTrue(is_op)
        self.assertEqual(label, "cross-promo")

    def test_cross_promo_re_does_not_match_normal_punct(self) -> None:
        """正常含 | 的 markdown 表格行不应误判 cross-promo。"""
        # 需要看正则到底
        for s in (
            "正常正文,字数较多,不含 | 拼接的 cross-promo 风格。",
            "短句末尾 |",
            "| 单个表格 cell |",
        ):
            with self.subTest(s=s):
                self.assertIsNone(_CROSS_PROMO_RE.match(s))

    def test_mid_conf_only_with_flag(self) -> None:
        s = "投稿邮箱:editor@example.com"
        # default mid_conf=False
        is_op_default, _ = _is_operational_paragraph(s)
        self.assertFalse(is_op_default, "默认不命中 mid-conf")
        # mid_conf=True
        is_op_explicit, label = _is_operational_paragraph(s, mid_conf=True)
        self.assertTrue(is_op_explicit)
        self.assertTrue(label.startswith("mid-conf"))


class TestZaikanFamily(unittest.TestCase):
    """T-N9: '在看' 系经典公众号尾巴 — ai-subprime 漏抓 must-fix 复现。"""

    def test_ai_subprime_must_fix_literal(self) -> None:
        """复现 ai-subprime 上线漏抓的字面 case(中文全角引号包住"在看")。"""
        s = '觉得好看，请点"在看"'
        is_op, label = _is_operational_paragraph(s)
        self.assertTrue(is_op, f"ai-subprime must-fix 漏抓:{label!r}")
        self.assertTrue(
            label.startswith("high-conf"),
            f"应该是 high-conf 而非 mid-conf:{label}",
        )

    def test_zaikan_variants(self) -> None:
        """各种 '在看' 引导词变体都应被识别。"""
        variants = [
            "请点在看",
            "请点 在看",
            '请点"在看"',  # ascii 双引号
            "请点'在看'",  # 中文单引号
            "点击在看",
            "点个在看",
            "点一下在看",
            "帮点在看",
            "帮点 在看",
            "动动手指点在看",
        ]
        for s in variants:
            with self.subTest(s=s):
                is_op, label = _is_operational_paragraph(s)
                self.assertTrue(is_op, f"{s!r} 应被识别;label={label!r}")

    def test_dianzan_combo(self) -> None:
        """点赞 + 在看/转发/收藏 三连各种组合。"""
        for s in (
            "点赞在看",
            "点赞、在看",
            "点赞和在看",
            "点赞 在看",
            "点赞、转发",
            "点赞、转发、收藏",
            "点赞 转发",
            "点赞和转发到朋友圈",
            "点赞收藏在看三连",
            "点赞收藏转发",
        ):
            with self.subTest(s=s):
                is_op, _ = _is_operational_paragraph(s)
                self.assertTrue(is_op, f"{s!r} 应被识别为运营段")

    def test_xingbiao_family(self) -> None:
        """'星标' 系运营段。"""
        for s in (
            "加为星标",
            "设为星标",
            "加星标",
            "星标我们的公众号",
            "星标公众号",
        ):
            with self.subTest(s=s):
                is_op, _ = _is_operational_paragraph(s)
                self.assertTrue(is_op, f"{s!r} 应被识别")

    def test_pengyouquan_family(self) -> None:
        """朋友圈系。"""
        for s in (
            "转发朋友圈",
            "分享朋友圈",
            "请转发朋友圈支持一下",
        ):
            with self.subTest(s=s):
                is_op, _ = _is_operational_paragraph(s)
                self.assertTrue(is_op, f"{s!r} 应被识别")

    def test_dianzan_zaikan_negative_body(self) -> None:
        """T-N9 negative cases:body 中性句**不应**误伤。"""
        body_sentences = [
            # 单字 '在看' 或单字 '点' 出现在正文,无 'X+在看' 组合
            "他在看那本书,不过看得不太细。",
            "我们点这个菜单上的特色菜。",
            "她说这部电影非常好看,推荐给大家。",
            "本文重点关注美股估值的回归路径,具体细节见下文。",
            # cursor review nit:`好看[...]` 收敛后,这些"好看 + 点"但无 "在看" 的
            # body 句不应被误判为运营段
            "这部电影好看,点击购票链接立刻预订。",
            "餐厅环境不错,菜单好看,请点这边的招牌菜。",
        ]
        for s in body_sentences:
            with self.subTest(s=s):
                is_op, label = _is_operational_paragraph(s)
                self.assertFalse(is_op, f"误伤 body:{s!r} → {label!r}")


class TestBodyDetection(unittest.TestCase):
    def test_long_normal_text_is_body(self) -> None:
        s = "这是一段足够长的正文段落,论述充分,字数已超过 30 字符的最低门槛。"
        self.assertTrue(_is_body_paragraph(s))

    def test_short_text_not_body(self) -> None:
        for s in ("01", "短句", "标题"):
            self.assertFalse(_is_body_paragraph(s))

    def test_long_op_text_not_body(self) -> None:
        s = "扫描二维码添加小助手微信,获取最新文章推送,长按识别即可。"
        self.assertFalse(_is_body_paragraph(s))


class TestTruncationLogic(unittest.TestCase):
    def test_no_op_tail_returns_none(self) -> None:
        paras = [
            "这是开头一段,内容足够长可以被识别为 body。" * 2,
            "这是中段,论述继续展开,关注估值与周期。" * 2,
            "这是结尾段,呼应主题,完整收束。" * 2,
        ]
        self.assertIsNone(_find_truncation_point(paras))

    def test_op_tail_after_body_returns_cut_idx(self) -> None:
        paras = [
            "正文开头段,字数足够长以满足 body 阈值,展开论述并给出依据。",
            "正文继续段,展开论述与举例,讨论估值回归与周期演变。",
            "正文结尾段,完整收束论点,字数足够长以通过 body 阈值。",
            "扫描二维码添加小助手微信",
            "点击下方关注公众号",
        ]
        cut_idx = _find_truncation_point(paras)
        self.assertEqual(cut_idx, 3, "应该从第 4 个段(index=3)起截断")

    def test_op_in_middle_not_truncated(self) -> None:
        """运营词出现在正文中部不应触发尾部截断。"""
        paras = [
            "正文开头,长度足够。" * 3,
            "中段提到扫描二维码这个 UX 模式但本身是正文。" * 2,  # >30 字+含 high-conf 词
            "正文结尾,长度够,讨论投资策略与风险控制。" * 2,
        ]
        # 注意:中段段落被 _is_body_paragraph 判定为非 body(因含 high-conf 词),
        # 但末段是 body,所以 last_body_idx = 2 (末段),end -1 = 2,无尾巴 → None
        self.assertIsNone(_find_truncation_point(paras))

    def test_only_op_tail_no_body_returns_none(self) -> None:
        """如果全篇没有"看起来像正文"的段,什么都不动。"""
        paras = ["扫描二维码", "点击关注公众号"]
        self.assertIsNone(_find_truncation_point(paras))

    def test_huang_renxun_case_real(self) -> None:
        """复现 huang-renxun 篇 must-fix 模式。"""
        paras = [
            "黄仁勋说我们已经实现了AGI,这一观点震惊业界。" * 2,
            "他认为程序员将扩展到十亿规模。" * 3,
            "讨论 Ilya 的谨慎路径与黄仁勋的激进判断对照。" * 2,
            "播客链接:https://www.youtube.com/watch?v=vif8NQcjVf0",
            "扫描二维码添加小助手微信",
        ]
        cut_idx = _find_truncation_point(paras)
        # 播客链接(45 字符,无 high-conf 词)也被识别为 body
        # 所以 last body = idx 3, cut from idx 4 ("扫描二维码")
        self.assertEqual(cut_idx, 4)

    def test_ai_subprime_case_real(self) -> None:
        """T-N9 复现 ai-subprime 篇 must-fix 模式(`觉得好看,请点"在看"` 漏抓)。"""
        # 模拟 ai-subprime 真实结构:正文 N 段 + 末尾"觉得好看，请点"在看""
        paras = [
            "微软近日宣布GitHub Copilot将于2026年6月转向基于用量的计费模式,"
            "这一转变撕开了生成式AI行业'补贴换增长'的假象。",
            "AI模式相当于优步收 20 美元月费允许你跑 100 趟长途,"
            "却要为每加仑 150 美元的油价买单。",
            "OpenAI 必须在 4 年内通过营收或融资筹集到 8520 亿美元。"
            "如果失败,甲骨文的股价大跌将引发连锁的保证金追缴。",
            "预警信号:OpenAI CFO Sarah Friar 已表达担忧,"
            "称如果收入增长不够快,公司可能无法支付未来的计算合同。",
            '觉得好看，请点"在看"',  # 上线漏抓的 must-fix
        ]
        cut_idx = _find_truncation_point(paras)
        self.assertEqual(
            cut_idx,
            4,
            "ai-subprime tail 漏抓回归:应从 idx 4 (觉得好看,请点'在看') 起截断",
        )

    def test_dianzan_zhuanfa_tail_real(self) -> None:
        """复合三连尾巴(点赞、转发、收藏)。"""
        paras = [
            "正文段落一,字数足够长,论述充分讨论核心论点。" * 2,
            "正文段落二,继续展开举例,提供数据和案例支撑。" * 2,
            "正文段落三,完整收束论点,字数足够长。" * 2,
            "如果觉得本文有帮助,请点赞、转发、收藏",
        ]
        cut_idx = _find_truncation_point(paras)
        self.assertEqual(cut_idx, 3, "三连 tail 应被截断")


class TestCmdNormalizeSourceFlow(unittest.TestCase):
    """端到端:cmd_normalize_source 在 tmp 仓库上的行为。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mx-norm-"))
        self.slug = "fixture-slug"
        draft = self.tmp / "content" / "drafts" / self.slug
        draft.mkdir(parents=True)
        self.src = draft / "01-source.md"
        # 写一个含运营尾巴的 source
        # 注:用显式 \n\n 分隔避免 Python literal concatenation 误生成多余段落
        body1 = "正文开头段,字数足够多以满足 body 阈值,这是第一段的论述展开内容。"
        body2 = "正文中段,继续展开论述,字数充裕,讨论估值与回归路径相关问题。"
        body3 = "正文结尾段,完整收束论点,字数足够长以通过 body 识别阈值。"
        op1 = "扫描二维码添加小助手微信"
        op2 = "点击下方关注公众号"
        self.src.write_text(
            f"{body1}\n\n{body2}\n\n{body3}\n\n{op1}\n\n{op2}\n",
            encoding="utf-8",
        )
        self._patch = mock.patch.object(mingox, "ROOT", self.tmp)
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_check_mode_does_not_modify_file(self) -> None:
        """默认 --check 模式应不改动文件;exit 1 表示发现可截断段。"""
        original = self.src.read_text(encoding="utf-8")
        args = argparse.Namespace(slug=self.slug, auto_truncate=False)
        with self.assertRaises(SystemExit) as cm:
            mingox.cmd_normalize_source(args)
        self.assertEqual(cm.exception.code, 1, "发现可截断段应 exit 1")
        # 文件未变
        self.assertEqual(self.src.read_text(encoding="utf-8"), original)

    def test_auto_truncate_writes_file(self) -> None:
        original = self.src.read_text(encoding="utf-8")
        args = argparse.Namespace(slug=self.slug, auto_truncate=True)
        with self.assertRaises(SystemExit) as cm:
            mingox.cmd_normalize_source(args)
        self.assertEqual(cm.exception.code, 0)
        new = self.src.read_text(encoding="utf-8")
        self.assertNotEqual(new, original, "--auto-truncate 应实际改动文件")
        self.assertNotIn("扫描二维码", new, "运营段应被移除")
        self.assertNotIn("点击下方关注公众号", new)
        # body 段应保留
        self.assertIn("正文结尾段", new)

    def test_clean_file_no_change(self) -> None:
        """已清洁的文件应 exit 0 + 文件不变。"""
        body1 = "正文开头段,字数足够多以满足 body 阈值,内容充实。"
        body2 = "正文中段,继续展开论述,字数充裕,讨论估值与回归。"
        body3 = "正文结尾段,完整收束论点,字数足够长以通过阈值。"
        clean = f"{body1}\n\n{body2}\n\n{body3}\n"
        self.src.write_text(clean, encoding="utf-8")
        args = argparse.Namespace(slug=self.slug, auto_truncate=True)
        with self.assertRaises(SystemExit) as cm:
            mingox.cmd_normalize_source(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(self.src.read_text(encoding="utf-8"), clean)


if __name__ == "__main__":
    unittest.main()
