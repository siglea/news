#!/usr/bin/env python3
"""
对话/文件侧标注结果合并：校验、全文 en 去重、覆盖率、生成段落 HTML。
供 annotate_engine=chat_json（对话 JSON）使用。
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


CHAT_SYSTEM_PROMPT = """你是双语财经/科技编辑，为 **chat_json** 产出逐句标注 JSON（用于网页词汇表）。**默认引擎永远是 chat_json**；除非编者明确要求，不得改用 keywords 词表匹配。

与站点 EDITORIAL「词汇标注规范」对齐的**硬要求**（优先于下述“宁缺毋滥”旧表述）：
1. **每一句必须有 1 处合格标注**：对 export-chat-bundle 给出的每个句子序号 i（0..N-1）输出一条带 zh/en/ipa/pos/gloss 的对象。**禁止无故 `skip:true`**；仅当该句去掉句末标点后**正文为空**时才可 skip。
2. 每句仍只嵌 **一个** word-block：整句里最值得学的一个锚点。
3. **全文英文词形 en 不得重复**（合并层按出现顺序去重，后出现的同形会丢）；规划时请让每句使用**尚未出现过**的 en。
4. **不要用 `synth-lexicon-annotations` / 全局词表匹配代替本条**：那是 keywords 式初稿工具，**不是** chat_json 成稿标准。

选词细则（仍须遵守）：
- 词性优先：名词、动词优先于形容词、副词。
- 领域优先：行业术语、专业表达优先于日常泛词。
- 排除 EDITORIAL 列出的「不识别」极常见英文（如 price、risk、trade、market 等单独凑数）；若句中无更好锚点，可用**中文子串 → 合规英文词**（对义项一致），勿空句。
- zh 必须是该句去掉句末。！？；后的正文里**逐字照抄的连续子串**，且为**最短**画线片段；与 en/ipa/pos/gloss 同指。
- （兼容）若误用长 zh + underline：underline 须为 zh 子串，合并时以 underline 为准；新产出请只写最短 zh。
- en 必须是一个英文 token（无空格），复合概念用连字符，如 supply-chain、soft-skill。
- **对义项锚定**：en 须是读者看到 zh 时最直接对应的英文词/复合词；禁止同句「相关但不同位」的顶替（参见 EDITORIAL 示例：学习轨迹→trajectory 而非 analytics 等）。
- **语体与语域**：中文为中性职场/报道语体时，勿用带苦役、贬义或过度文学色彩的英文顶替日常义（例：「在航天行业工作多年」对 **work** 任职义，勿用 *toil*）。
- **日常搭配勿用大词**：如「全世界的科学家」应对 **worldwide / global** 等与「遍及全球」义对齐的词，勿用 *macrocosm* 等哲学/宇宙论专名硬套。
- ipa 用方括号包裹；pos 如 n. / v. / adj.；gloss 为 en 的简短中文释义。

输出**仅** JSON 对象：
{"version":1,"annotations":[{"i":0,"zh":"...","en":"...","ipa":"[...]","pos":"n.","gloss":"..."}, ...]}
必须覆盖每一个 i（0 到 N-1）。"""


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


def export_chat_bundle_dict(paragraphs: list[str]) -> dict[str, Any]:
    all_sents, _ = flatten_paragraphs(paragraphs)
    return {
        "version": 1,
        "kind": "mingox_chat_annotate_bundle",
        "sentence_count": len(all_sents),
        "sentences": [{"i": i, "text": t} for i, t in enumerate(all_sents)],
        "instructions": (
            "将 system_prompt 与 sentences 发给对话，产出 JSON 存为 llm_annotations.json 后 build；"
            "或改用 meta.annotate_engine=keywords 使用仓库全局词表（util/keyword_lexicon.py）。"
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


