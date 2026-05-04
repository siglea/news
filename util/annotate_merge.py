#!/usr/bin/env python3
"""
对话 JSON（llm_annotations.json）合并进段落 HTML；`mingox build` 强制要求该文件存在后调用。
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import Any

import annotate_lib as al

_UTIL_DIR = Path(__file__).resolve().parent
_CHAT_PROMPT_PATH = _UTIL_DIR / "prompts" / "chat_annotate_system.txt"


def _load_chat_system_prompt() -> str:
    if not _CHAT_PROMPT_PATH.is_file():
        raise FileNotFoundError(
            f"annotate system prompt missing: {_CHAT_PROMPT_PATH} "
            "(expected UTF-8 text; edit this file to change model instructions)"
        )
    return _CHAT_PROMPT_PATH.read_text(encoding="utf-8").strip()

COVERAGE_FLOOR = 0.001
COVERAGE_TARGET = 0.02


def en_headword_token_ok(en: str) -> bool:
    """Single English token: ASCII alnum only, no spaces or hyphens (see chat_annotate_system.txt)."""
    if not en or " " in en or "-" in en:
        return False
    core = en.replace(".", "")
    if not core or not core.isascii() or not core.isalnum():
        return False
    if not any(c.isalpha() for c in core):
        return False
    return True


CHAT_SYSTEM_PROMPT = _load_chat_system_prompt()

# 文末图集 MVP：仅 `../images/posts/<stem>/…` 的 Markdown 图行不参与词汇句切分与标注索引
_GALLERY_MD_LINE = re.compile(
    r"^!\[[^\]]*\]\(\s*(\.\./)+images/posts/[^)\s]+\)\s*$",
)


def paragraph_is_mingox_gallery_markdown(para: str) -> bool:
    """是否为「仅含本站 images/posts 相对路径的 Markdown 图」段落（可含多行）。"""
    lines = [ln.strip() for ln in para.replace("\r", "").strip().split("\n") if ln.strip()]
    if not lines:
        return False
    return all(_GALLERY_MD_LINE.match(ln) for ln in lines)


def _strip_outer_bold(s: str) -> str:
    t = s.strip()
    if t.startswith("**") and t.endswith("**") and len(t) > 4:
        return t[2:-2].strip()
    return t


_RE_H2_ENUM = re.compile(r"^[一二三四五六七八九十百千两]+、")
_RE_H3_GATE = re.compile(r"^关卡\s*\d+\s*[:：]")
_RE_H3_CHAPTER = re.compile(r"^第\s*[一二三四五六七八九十百千两零〇○０-９0-9]+\s*章")
_RE_H3_STEP = re.compile(r"^Step\s+\d+\b", re.I)
_RE_H3_NUM_DOT = re.compile(r"^\d+\.\s+\S")


def _paragraph_never_heading(s: str) -> bool:
    """Lines that must never be promoted to h2/h3 (byline, caption, etc.)."""
    if not s or "\n" in s:
        return True
    if "责任编辑" in s:
        return True
    if "文 /" in s or "文/" in s or "微信公众号：" in s or "微信号：" in s:
        return True
    if s.startswith("图源") or s.startswith("图片来源"):
        return True
    if "芯片" in s and ("制造" in s or "用于" in s) and len(s) <= 22:
        return True
    return False


def paragraph_heading_level(para: str) -> int:
    """Section heading level for `article_layout: segments`: 0 body, 2 h2, 3 h3.

    Order: 一、… → h2; 关卡/章节/Step/短编号行/整段加粗短句/原问句短标题 → h3.
    """
    if paragraph_is_mingox_gallery_markdown(para):
        return 0
    s = para.replace("\r", "").replace("&nbsp;", " ").strip()
    if _paragraph_never_heading(s):
        return 0
    display = _strip_outer_bold(s)
    if not display:
        return 0
    if _RE_H2_ENUM.match(display):
        return 2
    if (
        _RE_H3_GATE.match(display)
        or _RE_H3_CHAPTER.match(display)
        or _RE_H3_STEP.match(display)
    ):
        return 3
    if (
        _RE_H3_NUM_DOT.match(display)
        and len(display) <= 28
        and not re.search(r"[。！？；]$", display)
    ):
        return 3
    if s.startswith("**") and s.endswith("**"):
        inner = _strip_outer_bold(s)
        if (
            inner
            and len(inner) < 25
            and not re.search(r"[。！？；]$", inner)
            and "\n" not in inner
        ):
            return 3
    if paragraph_is_section_subheading(para):
        return 3
    return 0


def paragraph_is_section_subheading(para: str) -> bool:
    """Heuristic: WeChat-style intertitle line (short, often a question or punchy phrase).

    Only consulted when `article_layout: segments` so legacy posts stay byte-stable.
    """
    if paragraph_is_mingox_gallery_markdown(para):
        return False
    s = para.replace("\r", "").replace("&nbsp;", " ").strip()
    if _paragraph_never_heading(s):
        return False
    if len(s) > 40 or len(s) < 4:
        return False
    if s.endswith("。") and len(s) > 12:
        return False
    if s.count("，") >= 2 and len(s) > 18:
        return False
    if (s.startswith("\u201c") or s.startswith('"') or s.startswith("“")) and len(s) > 22:
        return False
    if s[-1] in "?!？！":
        return len(s) <= 42
    if len(s) <= 14 and "。" not in s and s.count("，") <= 1:
        return True
    return False


def gallery_markdown_paragraph_to_figure_html(para: str) -> str:
    """将图集 Markdown 段落转为 <figure> 块（不做词汇标注）。"""
    figs: list[str] = []
    for ln in para.replace("\r", "").strip().split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", ln)
        if not m:
            continue
        alt, src = m.group(1), m.group(2).strip()
        figs.append(
            '<figure class="article-figure">'
            f'<img src="{html.escape(src, quote=True)}" loading="lazy" '
            f'alt="{html.escape(alt)}">'
            "</figure>"
        )
    return "\n".join(figs) if figs else f"<p>{html.escape(para)}</p>"


def flatten_paragraphs(
    paragraphs: list[str],
    *,
    layout_segments: bool = False,
) -> tuple[list[str], list[tuple[int, int]]]:
    sentences: list[str] = []
    origin: list[tuple[int, int]] = []
    for pi, para in enumerate(paragraphs):
        if paragraph_is_mingox_gallery_markdown(para):
            continue
        if layout_segments and paragraph_heading_level(para) > 0:
            continue
        for sj, s in enumerate(al.split_sentences(para.replace("\r", ""))):
            sentences.append(s.strip())
            origin.append((pi, sj))
    return sentences, origin


def normalize_annotation_item(item: dict[str, Any], sent_text: str) -> dict[str, str] | None:
    if item.get("skip") is True:
        return None
    zh = str(item.get("zh", "")).strip()
    en_raw = str(item.get("en", "")).strip()
    ipa = str(item.get("ipa", "")).strip()
    pos = str(item.get("pos", "")).strip()
    gloss = str(item.get("gloss", "")).strip()
    underline = str(item.get("underline", "")).strip()
    if not en_raw or not ipa or not pos:
        return None
    if " " in en_raw or not en_headword_token_ok(en_raw):
        return None
    body, _ = al.sentence_body_and_punct(sent_text)
    if underline:
        if underline not in body:
            return None
        if zh and (zh not in body or underline not in zh):
            return None
        out_zh = underline
    else:
        if not zh or zh not in body:
            return None
        out_zh = zh
    if not gloss.strip():
        return None
    if not ipa.startswith("["):
        ipa = f"[{ipa.strip('[]')}]"
    # Keep a stable dedupe key from original token (may include numeric suffix),
    # but render a cleaned headword without trailing digits.
    en_display = re.sub(r"\d+$", "", en_raw).strip() or en_raw
    return {
        "zh": out_zh,
        "en": en_display,
        "ipa": ipa,
        "pos": pos,
        "gloss": gloss.strip(),
        "_dedupe_key": en_raw.lower(),
    }


def rows_from_annotations_payload(
    all_sents: list[str],
    annotations: list[Any],
) -> list[dict[str, str] | None]:
    n = len(all_sents)
    row: list[dict[str, str] | None] = [None] * n
    if not isinstance(annotations, list):
        return row
    for item in annotations:
        if not isinstance(item, dict):
            continue
        try:
            ii = int(item.get("i"))
        except (TypeError, ValueError):
            continue
        if ii < 0 or ii >= n:
            continue
        row[ii] = normalize_annotation_item(item, all_sents[ii])
    return row


def dedupe_in_order(annos: list[dict[str, str] | None]) -> list[dict[str, str] | None]:
    used: set[str] = set()
    out: list[dict[str, str] | None] = []
    for a in annos:
        if not a:
            out.append(None)
            continue
        k = str(a.get("_dedupe_key") or a["en"].lower())
        if k in used:
            out.append(None)
        else:
            used.add(k)
            out.append(a)
    return out


def coverage_ratio(annos: list[dict[str, str] | None], full_text: str) -> float:
    han = len(re.findall(r"[\u4e00-\u9fff]", full_text))
    if han == 0:
        return 0.0
    covered = sum(len(a["zh"]) for a in annos if a)
    return covered / han


def paragraphs_html_from_annos(
    paragraphs: list[str],
    origin: list[tuple[int, int]],
    all_sents: list[str],
    annos: list[dict[str, str] | None],
    *,
    layout_segments: bool = False,
) -> list[str]:
    sent_to_global: dict[tuple[int, int], int] = {}
    for gi, (pi, sj) in enumerate(origin):
        sent_to_global[(pi, sj)] = gi

    html_parts: list[str] = []
    for pi, para in enumerate(paragraphs):
        if paragraph_is_mingox_gallery_markdown(para):
            html_parts.append(gallery_markdown_paragraph_to_figure_html(para))
            continue
        if layout_segments:
            lvl = paragraph_heading_level(para)
            if lvl == 2:
                inner = html.escape(_strip_outer_bold(para.replace("\r", "")).strip())
                html_parts.append(f'<h2 class="article-subheading">{inner}</h2>')
                continue
            if lvl == 3:
                inner = html.escape(_strip_outer_bold(para.replace("\r", "")).strip())
                html_parts.append(f'<h3 class="article-subheading">{inner}</h3>')
                continue
        sents = al.split_sentences(para.replace("\r", ""))
        parts: list[str] = []
        for sj, s in enumerate(sents):
            s = s.strip()
            if not s:
                continue
            gi = sent_to_global[(pi, sj)]
            a = annos[gi] if gi < len(annos) else None
            if a:
                parts.append(
                    al.render_annotated_sentence(
                        s,
                        a["zh"],
                        a["en"],
                        a["ipa"],
                        a["pos"],
                        a["gloss"],
                    )
                )
            else:
                parts.append(al.escape_plain_sentence(s))
        inner = "".join(parts)
        html_parts.append(f"<p>{inner}</p>" if inner else f"<p>{html.escape(para)}</p>")
    return html_parts


def apply_annotations_payload(
    paragraphs: list[str],
    payload: dict[str, Any],
    *,
    warn_low_coverage: bool = True,
    layout_segments: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    all_sents, origin = flatten_paragraphs(paragraphs, layout_segments=layout_segments)
    if not all_sents:
        return [f"<p>{html.escape(p)}</p>" for p in paragraphs], {
            "coverage": 0.0,
            "annotated": 0,
            "sentences": 0,
            "source": "chat_json",
        }

    full_text = "\n".join(paragraphs)
    annos = rows_from_annotations_payload(all_sents, payload.get("annotations", []))
    annos = dedupe_in_order(annos)
    cov = coverage_ratio(annos, full_text)
    html_list = paragraphs_html_from_annos(
        paragraphs, origin, all_sents, annos, layout_segments=layout_segments
    )
    n_ann = sum(1 for a in annos if a)
    dbg = {
        "coverage": round(cov, 4),
        "annotated": n_ann,
        "sentences": len(all_sents),
        "source": "chat_json",
    }
    if warn_low_coverage and cov < COVERAGE_FLOOR:
        print(
            f"[annotate_merge] warning: coverage {cov:.4f} < floor {COVERAGE_FLOOR} "
            f"(annotated Han / total Han)",
            file=sys.stderr,
        )
    if warn_low_coverage and cov < COVERAGE_TARGET:
        bare = [i for i, a in enumerate(annos) if a is None and all_sents[i]]
        if bare:
            print(
                f"[annotate_merge] hint: coverage {cov:.4f} < target {COVERAGE_TARGET}; "
                f"无标注句序号（可补 JSON）: {bare[:40]}{'...' if len(bare) > 40 else ''}",
                file=sys.stderr,
            )
    return html_list, dbg


def export_chat_bundle_dict(
    paragraphs: list[str],
    *,
    slug: str | None = None,
    layout_segments: bool = False,
) -> dict[str, Any]:
    all_sents, _ = flatten_paragraphs(paragraphs, layout_segments=layout_segments)
    slug_token = slug or "<slug>"
    instructions = (
        "你正在为本 bundle 所属草稿产出词汇标注（结果将注入静态站点的 word-block）。\n"
        "规则以 `system_prompt` 字段为准；以下为最简作业流程：\n"
        "\n"
        "1. 逐句产出：句序号 `i` 与 `sentences[].i` 一一对齐，每个 `i` 出现且仅出现一次。\n"
        "   目标 ≥80% 非 `skip`；`skip` 仅用于纯标点或无实词的极短句。\n"
        "   每条 `zh` 必须是对应句去掉句末标点后正文的【逐字连续子串】；\n"
        "   全篇 `en` 不重复（合并层只保留首次）；`en` 须为 ASCII 字母数字单 token，\n"
        "   禁占位符（如 `lex`/`term*`/`*zh` 尾缀/生造拼接词）。\n"
        "\n"
        "2. 句数较多（>60）时不要一次返回全部 JSON——按每 20 句一批生成并增量写入文件，\n"
        "   最终合并为单个 `{\"version\":1,\"annotations\":[...]}` 对象（结构见 `response_schema`），\n"
        "   不要外层 Markdown 代码块。\n"
        "\n"
        f"3. 写入路径：`content/drafts/{slug_token}/llm_annotations.json`。\n"
        "\n"
        "4. 写完后自跑闭环（任一失败即按 stderr 修正 JSON 重跑）：\n"
        f"   - `python3 workflow/mingox.py validate --annotations --slug {slug_token}`\n"
        f"   - `python3 workflow/mingox.py build --slug {slug_token}`\n"
        "\n"
        "5. 反复修改后非 skip 比例仍 < 60%，停止本路径并提示用户改用：\n"
        f"   `python3 workflow/bundle_lexicon_annotate.py --slug {slug_token}` 词表兜底。\n"
        "\n"
        "完整说明：docs/steps/02-annotate.md。"
    )
    return {
        "version": 1,
        "kind": "mingox_chat_annotate_bundle",
        "sentence_count": len(all_sents),
        "slug": slug,
        "sentences": [{"i": i, "text": t} for i, t in enumerate(all_sents)],
        "instructions": instructions,
        "system_prompt": CHAT_SYSTEM_PROMPT,
        "response_schema": {
            "version": 1,
            "annotations": [
                {"i": 0, "skip": True},
                {
                    "i": 1,
                    "zh": "规模化",
                    "en": "scaling",
                    "ipa": "[ˈskeɪlɪŋ]",
                    "pos": "n.",
                    "gloss": "规模化；扩张",
                },
            ],
        },
    }
