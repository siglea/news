#!/usr/bin/env python3
"""
对话 JSON（llm_annotations.json）合并进段落 HTML；供存在标注文件时的 mingox build 使用。
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


def flatten_paragraphs(paragraphs: list[str]) -> tuple[list[str], list[tuple[int, int]]]:
    sentences: list[str] = []
    origin: list[tuple[int, int]] = []
    for pi, para in enumerate(paragraphs):
        for sj, s in enumerate(al.split_sentences(para.replace("\r", ""))):
            sentences.append(s.strip())
            origin.append((pi, sj))
    return sentences, origin


def normalize_annotation_item(item: dict[str, Any], sent_text: str) -> dict[str, str] | None:
    if item.get("skip") is True:
        return None
    zh = str(item.get("zh", "")).strip()
    en = str(item.get("en", "")).strip()
    ipa = str(item.get("ipa", "")).strip()
    pos = str(item.get("pos", "")).strip()
    gloss = str(item.get("gloss", "")).strip()
    underline = str(item.get("underline", "")).strip()
    if not en or not ipa or not pos:
        return None
    if " " in en or not en_headword_token_ok(en):
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
    return {"zh": out_zh, "en": en, "ipa": ipa, "pos": pos, "gloss": gloss.strip()}


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
        k = a["en"].lower()
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
) -> list[str]:
    sent_to_global: dict[tuple[int, int], int] = {}
    for gi, (pi, sj) in enumerate(origin):
        sent_to_global[(pi, sj)] = gi

    html_parts: list[str] = []
    for pi, para in enumerate(paragraphs):
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
) -> tuple[list[str], dict[str, Any]]:
    all_sents, origin = flatten_paragraphs(paragraphs)
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
    html_list = paragraphs_html_from_annos(paragraphs, origin, all_sents, annos)
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


def export_chat_bundle_dict(paragraphs: list[str]) -> dict[str, Any]:
    all_sents, _ = flatten_paragraphs(paragraphs)
    return {
        "version": 1,
        "kind": "mingox_chat_annotate_bundle",
        "sentence_count": len(all_sents),
        "sentences": [{"i": i, "text": t} for i, t in enumerate(all_sents)],
        "instructions": (
            "将 `system_prompt` 与 `sentences` 交给任意大模型，产出 JSON 保存为 "
            "`content/drafts/<slug>/llm_annotations.json` 后执行 `mingox build`。"
            "详见 docs/steps/02-annotate.md。"
        ),
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
