#!/usr/bin/env python3
"""
MingoX 四步流水线入口（本地执行）。

  python workflow/mingox.py <command> ...

前置与步骤说明见 docs/PREREQUISITES.md 与 docs/PIPELINE.md。
"""
from __future__ import annotations

import argparse
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

    build_slug(args.slug, skip_validate=args.skip_validate)


def cmd_export_chat_bundle(args: argparse.Namespace) -> None:
    import json

    sys.path.insert(0, str(WORKFLOW_DIR))
    from paths import ROOT, UTIL_DIR

    sys.path.insert(0, str(UTIL_DIR))
    from annotate_merge import export_chat_bundle_dict
    from md_split import paragraphs_from_markdown

    draft = ROOT / "content" / "drafts" / args.slug
    src = draft / "01-source.md"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    paras = paragraphs_from_markdown(src.read_text(encoding="utf-8"))
    bundle = export_chat_bundle_dict(paras)
    out = draft / "llm-chat-bundle.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
    ann = draft / "llm_annotations.json"
    print("Next: paste `system_prompt` + `sentences` into Cursor chat; save reply as", ann)


def cmd_validate(args: argparse.Namespace) -> None:
    sys.path.insert(0, str(WORKFLOW_DIR))
    from validate import validate_file, validate_posts_glob

    if args.post:
        raise SystemExit(validate_file(Path(args.post)))
    raise SystemExit(validate_posts_glob())


def cmd_serve(args: argparse.Namespace) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "http.server", str(args.port), "--bind", args.host],
        cwd=str(ROOT),
    )
    raise SystemExit(r.returncode)


def _edgeone_deploy_summary(stdout: str, stderr: str) -> None:
    """部署成功后从 CLI 输出中提取并醒目打印可访问链接（含 eo_token 等参数）。"""
    blob = f"{stdout or ''}\n{stderr or ''}"
    url = None
    extras: list[str] = []
    for raw in blob.splitlines():
        line = raw.strip()
        if line.startswith("EDGEONE_DEPLOY_URL="):
            url = line.split("=", 1)[1].strip()
        elif line.startswith("EDGEONE_") and "=" in line and not line.startswith("EDGEONE_DEPLOY_URL="):
            extras.append(line)
    if url:
        print("\n======== EdgeOne 可访问链接（含预览参数，勿公开传播）========")
        print(url)
        if extras:
            print("-------- 同次部署其它 CLI 变量（参考）--------")
            for e in extras:
                print(e)
        print("================================================================\n")
    else:
        print(
            "\n[mingox deploy] 未在输出中解析到 EDGEONE_DEPLOY_URL，"
            "若部署成功请从上方 edgeone CLI 日志中自行复制预览链接。\n"
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
    if r.returncode == 0:
        _edgeone_deploy_summary(r.stdout or "", r.stderr or "")
    raise SystemExit(r.returncode)


def cmd_wechat(args: argparse.Namespace) -> None:
    cmd = [_py(), str(ROOT / "util" / "annotate-wechat-plain.py")]
    if args.profile:
        cmd.extend(["--profile", args.profile])
    r = subprocess.run(cmd, cwd=str(ROOT))
    raise SystemExit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(prog="mingox-workflow", description="MingoX content pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create content/drafts/<slug>/meta.json template (annotate_engine=chat_json; repo default — keywords only if editor explicitly requests per draft)",
    )
    p_init.add_argument("--slug", required=True)
    p_init.add_argument("--title-zh", required=True)
    p_init.add_argument("--title-en", required=True)
    p_init.add_argument(
        "--out-html",
        required=True,
        help="posts/YYYY-MM-DD-topic-kebab.html（题材英文 kebab，勿用草稿 slug/wechat-id 占位）",
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
    p_b.set_defaults(func=cmd_build)

    p_eb = sub.add_parser(
        "export-chat-bundle",
        help="Write llm-chat-bundle.json for Cursor chat annotate (with annotate_engine=chat_json)",
    )
    p_eb.add_argument("--slug", required=True)
    p_eb.set_defaults(func=cmd_export_chat_bundle)

    p_v = sub.add_parser("validate", help="Run adjacent word-block check on posts/*.html")
    p_v.add_argument("--post", help="single file instead of all posts")
    p_v.set_defaults(func=cmd_validate)

    p_s = sub.add_parser("serve", help="Step 4 local: static server on repo root")
    p_s.add_argument("--port", type=int, default=8765)
    p_s.add_argument("--host", default="127.0.0.1")
    p_s.set_defaults(func=cmd_serve)

    p_d = sub.add_parser("deploy", help="Step 4: EdgeOne Pages (needs npx + token or login)")
    p_d.add_argument("--project", default="mingox")
    p_d.set_defaults(func=cmd_deploy)

    p_w = sub.add_parser("wechat", help="Legacy: util/annotate-wechat-plain.py --profile")
    p_w.add_argument("--profile", default=None)
    p_w.set_defaults(func=cmd_wechat)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
