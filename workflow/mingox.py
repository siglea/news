#!/usr/bin/env python3
"""
MingoX 四步流水线入口（本地执行）。

  python workflow/mingox.py <command> ...

入门环境见 docs/GETTING-STARTED.md；编排与步骤见 docs/TOOLING.md。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

WORKFLOW_DIR = Path(__file__).resolve().parent
ROOT = WORKFLOW_DIR.parent

# EdgeOne CLI 版本：默认仍跟最新（兼容旧行为），但可通过环境变量
# `MX_EDGEONE_VERSION` 锁定一个已验证版本，避免上游 breaking 影响线上发布。
# 锁定示例：MX_EDGEONE_VERSION=2.0.7 python3 workflow/mingox.py deploy
# 文档参考：docs/steps/04-publish.md
EDGEONE_CLI_DEFAULT = "latest"


def _profile_enabled() -> bool:
    """`MX_PROFILE=1` 时把每步耗时输出到 stderr。

    设计原则:
    - 默认关闭(老用户/CI 行为不变)
    - 通过环境变量 opt-in,zero-config 即可启用
    - 不引入外部依赖,只用 stdlib `time.monotonic`
    """
    v = (os.environ.get("MX_PROFILE", "") or "").strip().lower()
    return v in ("1", "true", "yes", "on", "stderr")


@contextmanager
def _profile_step(name: str):
    """上下文管理器:计时一段步骤并按需打印 [profile] 行到 stderr。

    用法:
        with _profile_step("build"):
            ...

    关闭(默认):无开销,仅 yield 一次。
    开启(`MX_PROFILE=1`):打印 `[profile] step=<name> dur_ms=<n> rc=<0|raised>`。
    """
    if not _profile_enabled():
        yield
        return
    start = time.monotonic()
    rc_label = "0"
    try:
        yield
    except SystemExit as e:
        rc_label = str(e.code if e.code is not None else 0)
        raise
    except BaseException:
        rc_label = "raised"
        raise
    finally:
        dur_ms = int((time.monotonic() - start) * 1000)
        print(f"[profile] step={name} dur_ms={dur_ms} rc={rc_label}", file=sys.stderr)


def _py() -> str:
    return sys.executable


def cmd_init(args: argparse.Namespace) -> None:
    sys.path.insert(0, str(WORKFLOW_DIR))
    from acquire import init_meta_template

    init_meta_template(
        args.slug,
        title_zh=args.title_zh,
        title_en=args.title_en,
        out_html=args.out_html,
        source_url=args.source_url or "",
        title_emoji=args.title_emoji or "📈",
        include_source_footer=args.source_footer,
        footer_template=getattr(args, "footer_template", "verbatim"),
        source_author_display=getattr(args, "source_author_display", "") or "",
        footer_derivative_mp_unknown=bool(getattr(args, "footer_derivative_mp_unknown", False)),
        risk_blurb_secondary=getattr(args, "risk_blurb_secondary", "") or "",
    )


def cmd_acquire(args: argparse.Namespace) -> None:
    sys.path.insert(0, str(WORKFLOW_DIR))
    import acquire as ac

    if args.mode == "url" and not args.url:
        raise SystemExit("url mode requires --url")
    if args.mode == "search" and not args.query:
        raise SystemExit("search mode requires --query")

    if args.mode == "paste":
        body = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
        ac.acquire_paste(args.slug, body)
    elif args.mode == "url":
        ac.acquire_url(
            args.slug,
            args.url,
            headless=args.headless,
            wechat_mobile=not getattr(args, "no_mobile_wechat", False),
            wait_verify_sec=int(getattr(args, "wait_verify", 0) or 0),
            skip_wechat_images=bool(getattr(args, "skip_wechat_images", False)),
        )
    elif args.mode == "search":
        if args.list_only:
            for c in ac.search_candidates(args.query):
                print(f"[{c['index']}] {c['title']}\n    {c['href']}\n")
            return
        ac.acquire_search(args.slug, args.query, args.pick, headless=args.headless)
    else:
        raise SystemExit(args.mode)


def cmd_build(args: argparse.Namespace) -> None:
    sys.path.insert(0, str(WORKFLOW_DIR))
    from build_draft import build_slug

    build_slug(
        args.slug,
        skip_validate=args.skip_validate,
        skip_quality_gates=bool(getattr(args, "skip_quality_gates", False)),
        update_index=bool(getattr(args, "update_index", False)),
        dry_run_index=bool(getattr(args, "dry_run_index", False)),
    )


def cmd_export_chat_bundle(args: argparse.Namespace) -> None:
    import json

    util_dir = ROOT / "util"
    sys.path.insert(0, str(util_dir))
    from annotate_merge import export_chat_bundle_dict
    from md_split import paragraphs_from_markdown

    draft = ROOT / "content" / "drafts" / args.slug
    src = draft / "01-source.md"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    paras = paragraphs_from_markdown(src.read_text(encoding="utf-8"))
    bundle = export_chat_bundle_dict(paras, slug=args.slug)
    out = draft / "llm-chat-bundle.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
    print(
        f"hint: 把以下口令贴给任意 LLM 即可开始标注（harness 无关）:\n"
        f"  读取 {out.relative_to(ROOT)} 并严格按其中 instructions 字段执行；\n"
        f"  若描述与 system_prompt 冲突以 system_prompt 为准。完成后回报 non-skip 比例与门禁结果。\n"
        f"hint(推荐): 在支持 subagent 的 harness 内，运行\n"
        f"  python3 workflow/mingox.py print-annotate-prompt --slug {args.slug}\n"
        f"  把输出作为 subagent prompt 派活，主代理别接手逐句标注（保护主线程上下文）。",
        file=sys.stderr,
    )


def _load_meta(slug: str) -> dict:
    meta_path = ROOT / "content" / "drafts" / slug / "meta.json"
    if not meta_path.is_file():
        raise SystemExit(f"missing {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def cmd_print_annotate_prompt(args: argparse.Namespace) -> None:
    meta = _load_meta(args.slug)
    bundle_path = Path("content") / "drafts" / args.slug / "llm-chat-bundle.json"
    annot_path = Path("content") / "drafts" / args.slug / "llm_annotations.json"
    out_html = meta.get("out_html") or f"posts/{meta.get('date','')}-{args.slug}.html"

    prompt = (
        f"你是一名严格按 system_prompt 逐句标注的 subagent。任务：\n"
        f"\n"
        f"1. 读取 {bundle_path.as_posix()}\n"
        f"   该文件 `instructions` 字段是作业指南；`system_prompt` 是硬约束（冲突以 system_prompt 为准）；\n"
        f"   `sentences` 数组每条带 `i` 与 `text`；`response_schema` 是输出形态参考。\n"
        f"\n"
        f"2. 严格按 system_prompt 逐句生成 `annotations` 数组：\n"
        f"   - 每句最多一条；句子无可标实词时 `{{\"i\":k,\"skip\":true}}`。\n"
        f"   - `zh` 必须是该句去掉句末标点（。！？；）后正文里的**连续子串**。\n"
        f"   - `en` 仅 ASCII 字母/数字，**全文唯一**；禁止占位（lex/term + 数字、汉拼粘连等）。\n"
        f"   - 目标 non-skip ≥ 80%（system_prompt 量化期望，未达则尽量补全而非整句跳过）。\n"
        f"\n"
        f"3. 把结果写到 {annot_path.as_posix()}（覆盖；无则新建）。仅写这一份文件，不要改其它。\n"
        f"\n"
        f"4. 然后跑两条命令，两条都必须 exit 0：\n"
        f"     python3 workflow/mingox.py build --slug {args.slug}\n"
        f"     python3 workflow/mingox.py validate --post {out_html}\n"
        f"   失败则修订 annotations 后重写一次（最多重试 1 次）；仍失败就回报错误并停止。\n"
        f"\n"
        f"5. 完成后回报：\n"
        f"   - non-skip 比例（annotated / sentences）。\n"
        f"   - build 是否通过、vocab 数量。\n"
        f"   - validate 输出最后 5 行（含 adjacent check 结果）。\n"
        f"   **禁止**把整份 annotations 粘回来——主代理只需要总结。\n"
    )
    print(prompt)


def cmd_validate(args: argparse.Namespace) -> None:
    sys.path.insert(0, str(WORKFLOW_DIR))
    sys.path.insert(0, str(ROOT / "util"))
    from annotation_quality_gate import validate_all_draft_annotations
    from validate import validate_file, validate_posts_glob

    code = 0
    if bool(getattr(args, "annotations", False)) or bool(getattr(args, "all", False)):
        code |= validate_all_draft_annotations(
            ROOT / "content" / "drafts",
            slug=str(getattr(args, "slug", "") or "") or None,
        )
    if args.post:
        code |= validate_file(Path(args.post))
    elif (not getattr(args, "annotations", False)) or bool(getattr(args, "all", False)):
        code |= validate_posts_glob()
    raise SystemExit(code)


def cmd_serve(args: argparse.Namespace) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "http.server", str(args.port), "--bind", args.host],
        cwd=str(ROOT),
    )
    raise SystemExit(r.returncode)


# ============================================================
# normalize-source: 检测/截断 01-source.md 末尾的运营尾巴
# 设计原则:
# - **默认 `--check`**:仅诊断,不动文件(零破坏)
# - **`--auto-truncate`**:仅在尾部段命中**高置信运营 pattern** 时实际截断
# - **不在正文中部命中**:从尾部往前找,遇到第一个"看起来像正文"的段落即停
# - 公开 _OP_TAIL_HIGH_CONF / _OP_TAIL_MID_CONF 模块常量,便于扩展+测试
# ============================================================

# 高置信运营 pattern:命中即可自动截断(典型微信公众号尾巴运营段)
#
# T-N9(2026-04-30):补全公众号经典尾巴 pattern
# - "在看"系:`觉得好看,请点"在看"` / `请点在看` / `点击在看` / `点个在看` 等
# - 三连系:`点赞收藏` / `点赞在看` / `点赞、转发`
# - 星标系:`加星标` / `设为星标` / `星标我们`
# - 朋友圈系:`转发朋友圈` / `分享朋友圈`
# 使用 substring + regex 双层匹配,regex 处理引号/空格 split 的"在看"等变体
_OP_TAIL_HIGH_CONF = (
    "扫描二维码",
    "扫码关注",
    "扫码进群",
    "长按识别",
    "添加小助手",
    "添加微信",
    "加微信",
    "关注公众号",
    "关注我们",
    "星标我们",
    "星标公众号",
    "加为星标",
    "设为星标",
    "加星标",
    "点击下方",
    "点击阅读原文",
    "阅读原文",
    "点赞关注",
    "点赞收藏",
    "点赞转发",
    "三连关注",
    "好看请点",
    "在看哦",
    "转发朋友圈",
    "分享朋友圈",
    "成为会员",
    "订阅《",
    "订阅本",
    "诚邀各领域",
    "申报《",
    "集世界500强",
)

# 高置信正则 pattern:处理引号/空格/标点 split 的常见组合
# 例如 `请点"在看"`(中文引号 split 了"点"和"在看")、`点赞、在看`、`觉得好看,请点 在看` 等
#
# 引号字符类(覆盖中英文/全角各种变体):
#   ASCII:  `"` (U+0022) / `'` (U+0027)
#   全角:    `"` (U+201C) / `"` (U+201D) / `'` (U+2018) / `'` (U+2019)
#   书名号:  `「` `」` `『` `』` `《` `》` `〈` `〉`
_QUOTE_CHARS = r"\"'“”‘’「」『』《》〈〉"
_OP_TAIL_HIGH_CONF_RE = (
    # "请点'在看'" / "请点 在看" / "请点"在看"" / "请帮点在看"
    re.compile(rf"[请帮]\s*点\s*[{_QUOTE_CHARS}]?\s*在看"),
    # "点击在看" / "点个在看" / "点一下在看" / "点一次在看" / "点下在看"
    re.compile(rf"点(?:击|个|一[下个次]?|下)\s*[{_QUOTE_CHARS}]?\s*在看"),
    # "点赞在看" / "点赞、在看" / "点赞和在看" / "点赞+在看" / "点赞 在看"
    re.compile(r"点赞[\s　、,,+/和]{0,3}在看"),
    # "点赞、转发" / "点赞,转发" / "点赞和转发" / "点赞 转发"
    re.compile(r"点赞.{0,4}转发"),
    # "点赞收藏在看三连" / "点赞、收藏、转发"
    re.compile(r"点赞.{0,4}收藏.{0,4}[在看转发分享]"),
    # "觉得好看,请点'在看'" 系列引语 — `好看` + `请点` + `在看` 同句共现
    # (cursor review: 收敛成与 `在看` 同句共现以降误伤,避免命中 "电影好看,点个赞" 等)
    re.compile(r"好看[\s　,,。.;;、!!??]{0,3}[请帮]?\s*点[^。\n]{0,12}在看"),
    # "动动手指点个赞" / "动动手指点在看"
    re.compile(r"动动.{0,3}手指"),
)

# 中置信运营 pattern:仅 `--check` 报告建议,不自动截断
# (因可能在正文中合法出现,如"商务合作"在某些行业稿子里就是正文)
_OP_TAIL_MID_CONF = (
    "商务合作",
    "投稿邮箱",
    "招聘内容编辑",
    "推荐阅读",
    "相关阅读",
    "热点视频推荐",
)

# 正文识别启发:段落长度 ≥ 30 字符 + 不含 high-conf pattern + 不像 cross-promo
# (cross-promo 例如 "话题A | 话题B | 话题C" 三个标题用 | 拼接)
_BODY_MIN_LEN = 30
# `|` 分隔的 cross-promo 行(典型: "起底游戏周边 | 白银之城 | 离职字节创业")
# 每段 2-15 字符且不含正文标点(逗号/句号/顿号),避免误伤含 `|` 的正文。
_CROSS_PROMO_RE = re.compile(
    r"^[^|\n,，。.；;、]{2,15}(\s*\|\s*[^|\n,，。.；;、]{2,15}){1,}\s*$"
)


def _is_operational_paragraph(text: str, *, mid_conf: bool = False) -> tuple[bool, str]:
    """是否是运营段?返回 `(is_op, reason_label)`。

    `mid_conf=False`(默认):仅 high-conf 命中算运营。
    `mid_conf=True`:high-conf + mid-conf 都算(用于 --check 报告)。
    """
    s = text.strip()
    if not s:
        return False, ""
    # 高置信(子串)
    for kw in _OP_TAIL_HIGH_CONF:
        if kw in s:
            return True, f"high-conf:{kw}"
    # 高置信(正则) — 处理引号/标点 split 的"点 在看"等变体
    for pat in _OP_TAIL_HIGH_CONF_RE:
        m = pat.search(s)
        if m:
            return True, f"high-conf-re:{pat.pattern[:30]}"
    if mid_conf:
        for kw in _OP_TAIL_MID_CONF:
            if kw in s:
                return True, f"mid-conf:{kw}"
    # cross-promo 链接列表
    if _CROSS_PROMO_RE.match(s):
        return True, "cross-promo"
    return False, ""


def _is_body_paragraph(text: str) -> bool:
    """判断段落是否"看起来像正文"。"""
    s = text.strip()
    if len(s) < _BODY_MIN_LEN:
        return False
    is_op, _ = _is_operational_paragraph(s, mid_conf=False)
    if is_op:
        return False
    return True


def _find_truncation_point(paragraphs: list[str]) -> int | None:
    """返回需要从哪个 paragraph index 起截断;None 表示不需截断。

    算法:
    1. 从末尾往前扫,找出最后一个"看起来像正文"段落的 index `last_body_idx`
    2. 若 `last_body_idx` 之后存在任何 high-conf pattern 段或 cross-promo,
       则从 `last_body_idx + 1` 起截断
    3. 若 last_body_idx 之后只有空段或中等置信段,**不**自动截断(避免误伤)
    """
    if not paragraphs:
        return None
    last_body_idx = -1
    for i, p in enumerate(paragraphs):
        if _is_body_paragraph(p):
            last_body_idx = i
    if last_body_idx == -1:
        return None  # 全篇无明显正文,不动
    if last_body_idx == len(paragraphs) - 1:
        return None  # 末段就是正文,无尾巴
    # 检查 last_body_idx + 1 .. end 是否有 high-conf 或 cross-promo
    has_high_conf = False
    for p in paragraphs[last_body_idx + 1:]:
        is_op, label = _is_operational_paragraph(p, mid_conf=False)
        if is_op and (label.startswith("high-conf") or label == "cross-promo"):
            has_high_conf = True
            break
    if has_high_conf:
        return last_body_idx + 1
    return None


def cmd_normalize_source(args: argparse.Namespace) -> None:
    """检测/截断 `content/drafts/<slug>/01-source.md` 末尾的运营尾巴。

    默认 `--check` 模式:输出诊断,不动文件,exit 0(干净) 或 1(发现可截断段)。
    `--auto-truncate`:仅在 high-conf 命中时实际写文件。
    """
    draft = ROOT / "content" / "drafts" / args.slug
    src = draft / "01-source.md"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    text = src.read_text(encoding="utf-8")
    paragraphs = [p for p in text.split("\n\n")]
    cut_idx = _find_truncation_point(paragraphs)

    # 收集 mid-conf 建议(只报,不动)
    mid_conf_hits: list[tuple[int, str, str]] = []
    if cut_idx is None:
        # 全篇逐段扫一下 mid-conf
        for i, p in enumerate(paragraphs):
            is_op, label = _is_operational_paragraph(p, mid_conf=True)
            if is_op and label.startswith("mid-conf"):
                mid_conf_hits.append((i, label, p[:40]))

    print(f"[normalize-source] {src.relative_to(ROOT)}({len(paragraphs)} paragraphs)")
    if cut_idx is None:
        print("[normalize-source] no high-confidence operational tail detected")
        if mid_conf_hits:
            print(
                f"[normalize-source] {len(mid_conf_hits)} mid-confidence hint(s) "
                "(not auto-truncated; review manually):"
            )
            for i, label, sample in mid_conf_hits[:5]:
                print(f"  - paragraph #{i} {label}: {sample!r}")
        raise SystemExit(0)

    cut_count = len(paragraphs) - cut_idx
    print(
        f"[normalize-source] high-conf operational tail starts at paragraph #{cut_idx} "
        f"({cut_count} paragraphs to cut):"
    )
    for i, p in enumerate(paragraphs[cut_idx:], start=cut_idx):
        if not p.strip():
            continue
        sample = p.strip()[:60]
        is_op, label = _is_operational_paragraph(p, mid_conf=False)
        marker = label or "(empty/whitespace)"
        print(f"  - paragraph #{i} {marker}: {sample!r}")

    if not args.auto_truncate:
        print(
            "[normalize-source] check mode: not modifying file. "
            "Re-run with --auto-truncate to apply."
        )
        raise SystemExit(1)  # exit 1 让 CI / process script 知道发现了问题

    # 实际截断
    new_paragraphs = paragraphs[:cut_idx]
    # 去尾部空白段
    while new_paragraphs and not new_paragraphs[-1].strip():
        new_paragraphs.pop()
    new_text = "\n\n".join(new_paragraphs).rstrip() + "\n"
    src.write_text(new_text, encoding="utf-8")
    print(
        f"[normalize-source] truncated: "
        f"{len(paragraphs)} → {len(new_paragraphs)} paragraphs, "
        f"wrote {len(new_text)} bytes"
    )
    raise SystemExit(0)


def _extract_edgeone_preview_url(blob: str) -> str | None:
    """从 edgeone CLI 输出解析预览 URL（须含 eo_token 等查询参数）。"""
    text = blob or ""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("EDGEONE_DEPLOY_URL="):
            u = line.split("=", 1)[1].strip().strip('"').strip("'")
            if u.startswith("http"):
                return u
    m = re.search(r"https://[^\s'\"<>]+\?[^\s'\"<>]+eo_token=[^\s'\"<>]+", text)
    if m:
        return m.group(0).rstrip(").,;")
    return None


def _edgeone_deploy_summary(stdout: str, stderr: str, *, success: bool) -> None:
    """每次部署结束后固定输出「预览地址」行（含完整查询串）；便于复制与助手复述。"""
    blob = f"{stdout or ''}\n{stderr or ''}"
    url = _extract_edgeone_preview_url(blob)
    extras: list[str] = []
    for raw in blob.splitlines():
        line = raw.strip()
        if line.startswith("EDGEONE_") and "=" in line and not line.startswith("EDGEONE_DEPLOY_URL="):
            extras.append(line)

    if url:
        # 固定首行文案：每次 deploy 结束须能直接看到可复制预览地址
        print("\n预览地址（须完整复制整行 URL，含 ? 后全部参数；勿公开传播）")
        print(url)
        if extras:
            print("\n同次部署其它 CLI 变量（参考）:")
            for e in extras:
                print(" ", e)
        print()
    elif success:
        print(
            "\n[mingox deploy] 已成功但未解析到预览地址，请从上方日志查找 EDGEONE_DEPLOY_URL 或含 eo_token 的 https 链接。\n"
        )
    else:
        print(
            "\n[mingox deploy] 部署失败；若日志中出现含 eo_token 的预览链接可自行复制。\n"
        )


def _preview_url_for_path(preview_url: str, path: str) -> str:
    """把 preview URL 改写成同查询串下的指定路径。"""
    p = urlparse.urlsplit(preview_url)
    return urlparse.urlunsplit((p.scheme, p.netloc, path, p.query, p.fragment))


def _http_status(url: str, *, timeout_sec: float = 15.0) -> int:
    """返回 URL HTTP 状态码。"""
    req = urlrequest.Request(url, method="GET")
    try:
        with urlrequest.urlopen(req, timeout=timeout_sec) as resp:
            return int(getattr(resp, "status", 200) or 200)
    except urlerror.HTTPError as e:
        return int(e.code)
    except (urlerror.URLError, TimeoutError, ConnectionError):
        # 网络/DNS 波动时不抛异常，交由上层 smoke check 以 WARN 形式报告
        return -1


def _deploy_live_smoke_check(preview_url: str, *, post_path: str | None = None) -> None:
    """部署后线上抽检：post=200, internal=404。

    - 默认检查 `index.html` 为 200（当未提供 post_path 时作为公开资源基线）
    - 内部路径 `/util/annotate_lib.py` 与 `/content/drafts/` 应为 404
    - 仅输出 WARN，不中断 deploy 成功返回码
    """
    targets: list[tuple[str, int, str]] = []
    if post_path:
        post_norm = "/" + post_path.lstrip("/")
        targets.append((post_norm, 200, "public-post"))
    else:
        targets.append(("/index.html", 200, "public-index"))
    targets.extend(
        [
            ("/util/annotate_lib.py", 404, "internal-util"),
            ("/content/drafts/", 404, "internal-drafts"),
        ]
    )

    issues: list[str] = []
    for rel, expected, label in targets:
        u = _preview_url_for_path(preview_url, rel)
        got = _http_status(u)
        if got != expected:
            issues.append(f"{label} {rel} expect={expected} got={got}")
    if issues:
        print("[deploy smoke] WARN: " + " ; ".join(issues), file=sys.stderr)
    else:
        print("[deploy smoke] OK: public/internal checks passed", file=sys.stderr)


def _deploy_preflight(token_path: Path, build_script: Path) -> tuple[str, bool]:
    """deploy 前置 fail-fast 检查。

    返回:`(auth_method, has_explicit_token)`
        - `auth_method`:`"file"`/`"env"`/`"cli-cached"`/`"none"`
        - `has_explicit_token`:True 时调用方应把 `-t TOKEN` 加进 npx cmd
        否则不加,让 EdgeOne CLI 自己用 cached login 走

    fail-fast 条件:
    - npx 不在 PATH → 立即报错(不浪费 build_dist 时间)
    - build_dist.sh 不可读 → 报错
    - 无任何认证方式时 → emit warn(不立即 fail,留给 CLI 自己尝试 cached
      login;失败时 CLI 会给清晰报错)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. npx 必须在 PATH
    npx = shutil.which("npx")
    if not npx:
        errors.append(
            "npx 不在 PATH(需要 Node.js + npm)。安装:`brew install node` "
            "或访问 https://nodejs.org;详情见 docs/GETTING-STARTED.md"
        )

    # 2. build_dist.sh 必须可读
    if not build_script.is_file():
        errors.append(
            f"build_dist.sh 不存在:{build_script}(预期由 PR #9 引入)"
        )

    # 3. 认证方式探测(file > env > cli-cached fallback)
    auth = "none"
    has_explicit = False
    # Try file
    if token_path.is_file():
        content = token_path.read_text(encoding="utf-8").strip()
        if content:
            auth = "file"
            has_explicit = True
        else:
            warnings.append(f"{token_path} 存在但为空")
    # Try env
    if auth == "none":
        env_token = (os.environ.get("EDGEONE_API_TOKEN", "") or "").strip()
        if env_token:
            auth = "env"
            has_explicit = True
    # Fall back to cli-cached
    if auth == "none":
        warnings.append(
            "未发现 .edgeone/.token 或 EDGEONE_API_TOKEN 环境变量;"
            "若 CLI 已浏览器登录则继续,否则后续会被 CLI 拒绝"
        )
        auth = "cli-cached"

    # 4. 公开资源完整性(避免传一个空 dist)
    expected_public = [ROOT / "index.html", ROOT / "posts"]
    for p in expected_public:
        if not p.exists():
            errors.append(f"缺失公开资源:{p}(deploy 前必须存在)")

    if errors:
        for e in errors:
            print(f"[deploy preflight] FAIL: {e}", file=sys.stderr)
        raise SystemExit(2)
    for w in warnings:
        print(f"[deploy preflight] WARN: {w}", file=sys.stderr)
    print(f"[deploy preflight] OK auth={auth}", file=sys.stderr)
    return auth, has_explicit


def cmd_deploy(args: argparse.Namespace) -> None:
    token_path = ROOT / ".edgeone" / ".token"
    build_script = ROOT / "tools" / "build_dist.sh"

    # 前置 fail-fast 检查(npx + build_dist.sh + 认证 + 公开资源)。
    # 失败立即退出,不浪费后续 build / upload 时间。
    with _profile_step("deploy.preflight"):
        _, has_explicit_token = _deploy_preflight(token_path, build_script)

    # Step 1: 本地预先构建 ./dist（白名单 opt-in:仅外网应见的静态资源）。
    # EdgeOne 平台侧也会跑一遍 `buildCommand`(见 edgeone.json),但本地先构建
    # 一份能让我们在 push 前看到 dist/ 内容是否符合预期；同时也兼容那些
    # 不走 buildCommand 的环境(直接上传 outputDirectory 内容的场景)。
    if build_script.is_file():
        print("[deploy] running tools/build_dist.sh ...")
        with _profile_step("deploy.build_dist"):
            rc = subprocess.run(
                ["bash", str(build_script)], cwd=str(ROOT)
            ).returncode
        if rc != 0:
            print(
                f"[deploy] tools/build_dist.sh exited {rc}; abort.", file=sys.stderr
            )
            raise SystemExit(rc)

    # 允许通过 `MX_EDGEONE_VERSION` 环境变量锁定一个已验证版本；
    # 未设置时仍跟 `edgeone@latest`（与历史行为兼容）。
    version = os.environ.get("MX_EDGEONE_VERSION", EDGEONE_CLI_DEFAULT).strip() or EDGEONE_CLI_DEFAULT
    cmd = [
        "npx",
        "--yes",
        f"edgeone@{version}",
        "pages",
        "deploy",
        "-a",
        "overseas",
        "-n",
        args.project,
    ]
    # 优先使用显式 token(file > env > cli-cached);has_explicit_token 时
    # 已在 preflight 验证非空,这里直接读
    if has_explicit_token:
        if token_path.is_file():
            token = token_path.read_text(encoding="utf-8").strip()
        else:
            token = os.environ.get("EDGEONE_API_TOKEN", "").strip()
        cmd.extend(["-t", token])
    print("running:", " ".join(cmd[:6]), "...")
    with _profile_step("deploy.npx_upload"):
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.stdout:
        print(r.stdout, end="" if r.stdout.endswith("\n") else "\n")
    if r.stderr:
        print(r.stderr, end="" if r.stderr.endswith("\n") else "\n", file=sys.stderr)
    _edgeone_deploy_summary(r.stdout or "", r.stderr or "", success=(r.returncode == 0))
    if r.returncode == 0:
        preview_url = _extract_edgeone_preview_url(f"{r.stdout or ''}\n{r.stderr or ''}")
        if preview_url:
            with _profile_step("deploy.live_smoke"):
                _deploy_live_smoke_check(preview_url, post_path=args.post_check)
        else:
            print("[deploy smoke] WARN: 未解析到 preview URL，跳过线上抽检", file=sys.stderr)
    raise SystemExit(r.returncode)


def _run_step(cmd: list[str]) -> int:
    r = subprocess.run(cmd, cwd=str(ROOT))
    return int(r.returncode or 0)


def cmd_close_loop(args: argparse.Namespace) -> None:
    draft = ROOT / "content" / "drafts" / args.slug
    meta_path = draft / "meta.json"
    src_path = draft / "01-source.md"
    ann_path = draft / "llm_annotations.json"
    if not draft.is_dir():
        raise SystemExit(f"missing draft dir: {draft}")
    if not meta_path.is_file():
        raise SystemExit(f"missing {meta_path}")
    if not src_path.is_file():
        raise SystemExit(f"missing {src_path}")
    if not ann_path.is_file():
        raise SystemExit(
            f"missing {ann_path}: run `python3 workflow/mingox.py export-chat-bundle --slug {args.slug}` "
            "and complete annotation first."
        )

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    out_html = str(meta.get("out_html", "")).strip()
    if not out_html:
        raise SystemExit("meta.json 缺少 out_html。")

    py = _py()
    wf = str(WORKFLOW_DIR / "mingox.py")

    # 优化:在 build 之前先跑 annotations gate(`validate --annotations --slug <slug>`)
    # 让标注层错误 fail-fast,免去先跑 build(产 HTML)→ 再 validate(发现问题)→
    # 修标注 → 再 build 的浪费。build 自己仍会跑标注 quality gate(双保险)。
    steps: list[tuple[str, list[str]]] = [
        ("annotations-gate", [py, wf, "validate", "--annotations", "--slug", args.slug]),
        ("build", [py, wf, "build", "--slug", args.slug]),
        ("validate", [py, wf, "validate", "--post", out_html]),
    ]
    if args.deploy:
        deploy_cmd = [py, wf, "deploy", "--project", args.project]
        deploy_cmd.extend(["--post-check", out_html])
        steps.append(("deploy", deploy_cmd))

    for name, cmd in steps:
        print(f"[close-loop] running {name}: {' '.join(cmd[2:])}")
        # 每个子步骤独立计时(MX_PROFILE=1 时生效);失败立即 raise,profile 也会
        # 在 finally 里把 dur_ms 打印出来
        with _profile_step(f"close-loop.{name}"):
            rc = _run_step(cmd)
            if rc != 0:
                raise SystemExit(rc)

    print(
        "[close-loop] OK: annotations-gate + build + validate"
        + (" + deploy" if args.deploy else "")
    )


def main() -> None:
    ap = argparse.ArgumentParser(prog="mingox-workflow", description="MingoX content pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create content/drafts/<slug>/meta.json template",
    )
    p_init.add_argument(
        "--slug",
        required=True,
        help="草稿目录名（小写连字符）；须由文章标题凝练，见 content/drafts/README.md「命名规范」",
    )
    p_init.add_argument("--title-zh", required=True)
    p_init.add_argument("--title-en", required=True)
    p_init.add_argument(
        "--out-html",
        required=True,
        help="posts/YYYY-MM-DD-<题材英文 kebab>.html；题材须来自 title_zh/title_en，勿用 wechat-id/mp 随机串，见 content/drafts/README.md",
    )
    p_init.add_argument("--source-url", default="")
    p_init.add_argument("--title-emoji", default="📈")
    p_init.add_argument(
        "--source-footer",
        action="store_true",
        help="Include WeChat-style source footer (needs source_url when publishing)",
    )
    p_init.add_argument(
        "--footer-template",
        choices=("verbatim", "derivative"),
        default="verbatim",
        help="derivative: 与私募招聘稿一致的「衍生整理」版权说明块",
    )
    p_init.add_argument(
        "--footer-derivative-mp-unknown",
        action="store_true",
        help="derivative 且暂未确认公众号名：首段不写具体「公众号」名称",
    )
    p_init.add_argument(
        "--source-author-display",
        default="",
        help="derivative：界面显示作者署名，写入版权首段",
    )
    p_init.add_argument(
        "--risk-blurb-secondary",
        default="",
        help="版权区风险提示第二段；默认可留空使用模板默认值",
    )
    p_init.set_defaults(func=cmd_init)

    p_acq = sub.add_parser("acquire", help="Step 1: write 01-source.md")
    p_acq.add_argument("--slug", required=True)
    p_acq.add_argument("--mode", choices=("paste", "url", "search"), required=True)
    p_acq.add_argument("--file", help="paste: read from file (else stdin)")
    p_acq.add_argument("--url", help="url mode")
    p_acq.add_argument("--query", help="search mode")
    p_acq.add_argument("--pick", type=int, default=0, help="search: result index")
    p_acq.add_argument("--list-only", action="store_true", help="search: print hits only, no fetch")
    p_acq.add_argument("--headless", action="store_true", help="WeChat Playwright headless")
    p_acq.add_argument(
        "--no-mobile-wechat",
        action="store_true",
        help="WeChat: skip iPhone UA 尝试，仅用桌面 Chromium",
    )
    p_acq.add_argument(
        "--wait-verify",
        type=int,
        default=0,
        metavar="SEC",
        help="WeChat: 若出现验证页，最多等待 SEC 秒供本机手动点验证（需非 headless）",
    )
    p_acq.add_argument(
        "--skip-wechat-images",
        action="store_true",
        help="WeChat: 不下载配图、不写文内 Markdown 图（默认按原文 <img> 顺序交错落盘到 images/posts/<out_html stem>/）",
    )
    p_acq.set_defaults(func=cmd_acquire)

    p_b = sub.add_parser("build", help="Step 2–3: tasks JSON + HTML from draft")
    p_b.add_argument("--slug", required=True)
    p_b.add_argument("--skip-validate", action="store_true")
    p_b.add_argument("--skip-quality-gates", action="store_true")
    p_b.add_argument(
        "--update-index",
        action="store_true",
        help="生成 <li> 注入 index.html 顶部(默认 off,需显式开启)",
    )
    p_b.add_argument(
        "--dry-run-index",
        action="store_true",
        help="与 --update-index 同用:仅预览注入,不动 index.html",
    )
    p_b.set_defaults(func=cmd_build)

    p_eb = sub.add_parser(
        "export-chat-bundle",
        help="写出 llm-chat-bundle.json（含四六级词汇标注 system_prompt），供大模型生成 llm_annotations.json",
    )
    p_eb.add_argument("--slug", required=True)
    p_eb.set_defaults(func=cmd_export_chat_bundle)

    p_pap = sub.add_parser(
        "print-annotate-prompt",
        help="打印一段自包含的 subagent prompt：派给 subagent 做逐句标注（保护主代理上下文，harness 通用）",
    )
    p_pap.add_argument("--slug", required=True)
    p_pap.set_defaults(func=cmd_print_annotate_prompt)

    p_ns = sub.add_parser(
        "normalize-source",
        help="检测/截断 01-source.md 末尾运营尾巴(扫码/关注/小助手 等)",
    )
    p_ns.add_argument("--slug", required=True)
    p_ns.add_argument(
        "--auto-truncate",
        action="store_true",
        help="实际写入截断后的文件;默认仅诊断输出(--check 模式)",
    )
    p_ns.set_defaults(func=cmd_normalize_source)

    p_v = sub.add_parser(
        "validate",
        help="检查 posts 版式；可选用 --annotations 全量查草稿 JSON，或 --all 二合一",
    )
    p_v.add_argument("--post", help="single file instead of all posts")
    p_v.add_argument(
        "--annotations",
        action="store_true",
        help="全量检查 content/drafts/**/llm_annotations.json（占位/假 en、重复 en 等，与 build 前一致）",
    )
    p_v.add_argument(
        "--all",
        action="store_true",
        help="同次执行 --annotations 与 posts 检查",
    )
    p_v.add_argument(
        "--slug",
        metavar="SLUG",
        help="与 --annotations 同用时，只检查 content/drafts/<SLUG>/llm_annotations.json",
    )
    p_v.set_defaults(func=cmd_validate)

    p_s = sub.add_parser("serve", help="Step 4 local: static server on repo root")
    p_s.add_argument("--port", type=int, default=8765)
    p_s.add_argument("--host", default="127.0.0.1")
    p_s.set_defaults(func=cmd_serve)

    p_d = sub.add_parser("deploy", help="Step 4: EdgeOne Pages (needs npx + token or login)")
    p_d.add_argument("--project", default="mingox")
    p_d.add_argument(
        "--post-check",
        help="可选：部署后抽检的成稿路径（如 posts/2026-04-30-foo.html）",
    )
    p_d.set_defaults(func=cmd_deploy)

    p_cl = sub.add_parser(
        "close-loop",
        help="闭环执行：annotations-gate -> build -> validate -> (optional) deploy",
    )
    p_cl.add_argument("--slug", required=True)
    p_cl.add_argument("--deploy", action="store_true", help="通过 build+validate 后继续部署")
    p_cl.add_argument("--project", default="mingox")
    p_cl.set_defaults(func=cmd_close_loop)

    args = ap.parse_args()
    # 包一层 step profiler:`MX_PROFILE=1` 时输出每个 cmd 的耗时;关闭时零开销
    with _profile_step(args.cmd or "unknown"):
        args.func(args)


if __name__ == "__main__":
    main()
