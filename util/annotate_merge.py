#!/usr/bin/env python3
"""
对话/文件侧标注结果合并：校验、全文 en 去重、覆盖率、生成段落 HTML。
供 annotate_engine=chat_json（对话 JSON）或 terms_json（词表 JSON）使用。
"""
from __future__ import annotations

import html
import json
import sys
from typing import Any

import annotate_lib as al

COVERAGE_FLOOR = 0.01
COVERAGE_TARGET = 0.03


def en_headword_token_ok(en: str) -> bool:
    """en：无空格；允许 nonGAAP 式句点；允许 soft-skill 式连字符（每段须为字母数字）。"""
    if " " in en or not en:
        return False
    core = en.replace(".", "")
    if not core:
        return False
    for part in core.split("-"):
        if not part.isalnum():
            return False
    return True


CHAT_SYSTEM_PROMPT = """你是双语财经/科技编辑，为中文句子挑选至多 1 个最值得读者学习的英文对应词（用于网页词汇表）。

规则（宁缺毋滥）：
1. 每句最多选 1 个：整句里最核心、或对句意影响最大的词/短语；没有合格项则 skip。
2. 词性优先：名词、动词优先于形容词、副词。
3. 领域优先：行业术语、专业表达优先于日常泛词。
4. 排除高中英语已覆盖的极常见概念对应的中文（如「公司」「时间」「很多」「可以」等），除非该词在句中有特殊专业含义。
5. zh 必须是该句去掉句末。！？；后的正文里**逐字照抄的连续子串**；且 **zh 即要画线的最短片段，不得夹带前后多余字**；与 en/ipa/pos/gloss 指同一词。
5b. （兼容）若误用长 zh + underline：underline 须为 zh 子串，合并时会改为只保留 underline 作为 zh。新产出请只写最短 zh，不要写 underline。
6. en 必须是一个英文 token（不允许空格），复合概念用连字符，如 supply-chain、soft-skill。
7. **对义项锚定（重要）**：en 必须是读者看到这段 zh 时**最直接对应的英文词/复合词**（同位释义），用于词汇表「中文—英文」对齐。**禁止**选用同句或同话题里「相关但不同位」的词：例如「学习轨迹」对 trajectory/path，不对 analytics；「数字员工」对数字分身/虚拟岗位，不对 staffing；「财务业绩」在财报语境对 earnings，不对泛称 results；「品牌出海」对 outbound（外向扩张），不单用泛称 globalization；「龙头壁垒」优先对 barrier 等「壁垒」的字面/商业义项，而非未出现「护城河」比喻时的 moat。
8. ipa 用方括号包裹的国际音标（英/美均可）；pos 如 n. / v. / adj.；gloss 为英文词 en 的简短中文释义，不得空。

输出**仅** JSON 对象，格式：
{"annotations":[{"i":0,"zh":"...","en":"...","ipa":"[...]","pos":"n.","gloss":"..."},{"i":1,"skip":true},...]}
必须覆盖每一个句子序号 i（从 0 到 N-1，逐项给出）。"""


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
    han = al.count_han_chars(full_text)
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
                        underline=a.get("underline"),
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
    """
    payload: {"version":1, "annotations":[{i, ...}|{i, skip:true}, ...]}
    """
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
            f"(annotated Han / total Han); 可在对话中补全无词句后更新 JSON 再 build",
            file=sys.stderr,
        )
    if warn_low_coverage and cov < COVERAGE_TARGET:
        bare = [i for i, a in enumerate(annos) if a is None and all_sents[i]]
        if bare:
            print(
                f"[annotate_merge] hint: coverage {cov:.4f} < target {COVERAGE_TARGET}; "
                f"无词句序号（供对话二轮）: {bare[:40]}{'...' if len(bare) > 40 else ''}",
                file=sys.stderr,
            )
    return html_list, dbg


def parse_terms_rows(rows: list[Any]) -> list[tuple[str, str, str, str, str, str]]:
    """(match_key, zh, en, ipa, pos, gloss)。en 须与 zh 同位锚定，见 CHAT 规则 7 与 en_headword_token_ok。"""
    out: list[tuple[str, str, str, str, str, str]] = []
    if not isinstance(rows, list):
        raise ValueError("terms must be a JSON array")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each terms array item must be a JSON object")
        zh = str(row.get("zh", "")).strip()
        en = str(row.get("en", "")).strip()
        ipa = str(row.get("ipa", "")).strip()
        pos = str(row.get("pos", "")).strip()
        gloss = str(row.get("gloss", "")).strip()
        match_key = str(row.get("match") or zh).strip()
        if not zh or not en or not ipa or not pos or not gloss:
            raise ValueError(f"terms row incomplete: en={en!r}")
        if zh not in match_key:
            raise ValueError(f"terms: zh must be substring of match for en={en!r}")
        if not en_headword_token_ok(en):
            raise ValueError(f"terms: invalid en headword token for en={en!r}")
        out.append((match_key, zh, en, ipa, pos, gloss))
    return out


def build_payload_from_terms_rows(
    paragraphs: list[str],
    rows: list[Any],
) -> dict[str, Any]:
    """Greedy longest-match over flattened sentences; one en (lower) per article."""
    all_sents, _ = flatten_paragraphs(paragraphs)
    terms_sorted = sorted(parse_terms_rows(rows), key=lambda t: len(t[0]), reverse=True)
    used_en: set[str] = set()
    ann: list[dict[str, Any]] = []

    for i, sent in enumerate(all_sents):
        body, _ = al.sentence_body_and_punct(sent)
        chosen: dict[str, Any] | None = None
        for match_key, zh, en, ipa, pos, gloss in terms_sorted:
            if en.lower() in used_en:
                continue
            if match_key not in body or zh not in body:
                continue
            ipa_out = ipa if ipa.startswith("[") else f"[{ipa.strip('[]')}]"
            chosen = {
                "i": i,
                "zh": zh,
                "en": en,
                "ipa": ipa_out,
                "pos": pos,
                "gloss": gloss,
            }
            used_en.add(en.lower())
            break
        if chosen:
            ann.append(chosen)
        else:
            ann.append({"i": i, "skip": True})

    return {"version": 1, "annotations": ann}


def export_chat_bundle_dict(paragraphs: list[str]) -> dict[str, Any]:
    all_sents, _ = flatten_paragraphs(paragraphs)
    return {
        "version": 1,
        "kind": "mingox_chat_annotate_bundle",
        "sentence_count": len(all_sents),
        "sentences": [{"i": i, "text": t} for i, t in enumerate(all_sents)],
        "instructions": (
            "若 meta.annotate_engine=terms_json：请编辑 content/drafts/<slug>/terms.json 后 build，无需本 bundle。"
            "若使用 chat_json：将 system_prompt 与 sentences 发给对话，产出 JSON 存为 llm_annotations.json 后 build。"
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


