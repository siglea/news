#!/usr/bin/env python3
"""
MingoX 四步流水线入口（本地执行）。

  python workflow/mingox.py <command> ...

前置与步骤说明见 docs/PREREQUISITES.md 与 docs/PIPELINE.md。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

WORKFLOW_DIR = Path(__file__).resolve().parent
ROOT = WORKFLOW_DIR.parent


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


def cmd_deploy(args: argparse.Namespace) -> None:
    token_path = ROOT / ".edgeone" / ".token"
    cmd = [
        "npx",
        "--yes",
        "edgeone@latest",
        "pages",
        "deploy",
        "-a",
        "overseas",
        "-n",
        args.project,
    ]
    if token_path.is_file():
        token = token_path.read_text(encoding="utf-8").strip()
        cmd.extend(["-t", token])
    print("running:", " ".join(cmd[:6]), "...")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.stdout:
        print(r.stdout, end="" if r.stdout.endswith("\n") else "\n")
    if r.stderr:
        print(r.stderr, end="" if r.stderr.endswith("\n") else "\n", file=sys.stderr)
    _edgeone_deploy_summary(r.stdout or "", r.stderr or "", success=(r.returncode == 0))
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

    steps: list[tuple[str, list[str]]] = [
        ("build", [py, wf, "build", "--slug", args.slug]),
        ("validate", [py, wf, "validate", "--post", out_html]),
    ]
    if args.deploy:
        steps.append(("deploy", [py, wf, "deploy", "--project", args.project]))

    for name, cmd in steps:
        print(f"[close-loop] running {name}: {' '.join(cmd[2:])}")
        rc = _run_step(cmd)
        if rc != 0:
            raise SystemExit(rc)

    print("[close-loop] OK: build + validate" + (" + deploy" if args.deploy else ""))


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
    p_acq.set_defaults(func=cmd_acquire)

    p_b = sub.add_parser("build", help="Step 2–3: tasks JSON + HTML from draft")
    p_b.add_argument("--slug", required=True)
    p_b.add_argument("--skip-validate", action="store_true")
    p_b.add_argument("--skip-quality-gates", action="store_true")
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
    p_d.set_defaults(func=cmd_deploy)

    p_cl = sub.add_parser(
        "close-loop",
        help="闭环执行：build -> validate -> (optional) deploy",
    )
    p_cl.add_argument("--slug", required=True)
    p_cl.add_argument("--deploy", action="store_true", help="通过 build+validate 后继续部署")
    p_cl.add_argument("--project", default="mingox")
    p_cl.set_defaults(func=cmd_close_loop)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
