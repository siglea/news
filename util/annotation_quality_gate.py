#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter
from typing import Any

_PLACEHOLDER_EN_RE = re.compile(r"^term\d*$", re.IGNORECASE)
_TRUNCATED_ENDING = tuple("的了着过和与及并而或在是就又还让把被")
_ZH_MULTI_TERM_MARKERS = ("、", "，", ",", "和", "与", "及", "并", "或")
_SENT_END_PUNCT = "。！？；!?;"
_EN_TOKEN_RE = re.compile(r"^[A-Za-z0-9.]+$")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _sentence_body(text: str) -> str:
    s = _norm(text)
    while s and s[-1] in _SENT_END_PUNCT:
        s = s[:-1]
    return s


def _en_token_ok(en: str) -> bool:
    if not en or " " in en or "-" in en:
        return False
    if not _EN_TOKEN_RE.fullmatch(en):
        return False
    return any(ch.isalpha() for ch in en)


def check_quality(
    meta: dict[str, Any],
    payload: dict[str, Any],
    *,
    sentences: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    meta_desc = _norm(meta.get("meta_description"))
    if not meta_desc:
        errors.append("meta_description 不能为空。")

    annotations = payload.get("annotations")
    if not isinstance(annotations, list):
        errors.append("llm_annotations.json 缺少 annotations 数组。")
        return errors, warnings

    non_skip: list[dict[str, Any]] = []
    for item in annotations:
        if isinstance(item, dict) and item.get("skip") is not True:
            non_skip.append(item)

    bad_placeholder: list[int] = []
    suspicious_cut: list[int] = []
    en_tokens: list[str] = []
    for item in non_skip:
        idx = int(item.get("i", -1))
        zh = _norm(item.get("zh"))
        en = _norm(item.get("en"))
        ipa = _norm(item.get("ipa"))
        gloss = _norm(item.get("gloss"))
        en_tokens.append(en.lower())

        if _PLACEHOLDER_EN_RE.match(en) or ipa.lower().strip("[]") == "term":
            bad_placeholder.append(idx)
        if len(zh) >= 4 and zh[-1] in _TRUNCATED_ENDING:
            suspicious_cut.append(idx)
        if not zh:
            errors.append(f"句 {idx}: 缺少 zh。")
        if not _en_token_ok(en):
            errors.append(f"句 {idx}: en 非法（需单 token、ASCII 字母数字，可带点号）。")
        if any(ch in zh for ch in _ZH_MULTI_TERM_MARKERS) and len(zh) >= 3:
            errors.append(f"句 {idx}: zh 疑似包含多个并列概念（{zh}），不满足 zh/en 一一对应。")
        if len(zh) >= 8:
            warnings.append(f"句 {idx}: zh 偏长（{zh}），建议确认是否可收窄到最小对应词。")
        if zh and gloss and zh == gloss and len(zh) >= 8:
            warnings.append(f"句 {idx}: gloss 与 zh 完全一致且较长，建议复核释义精度。")
        if sentences is not None:
            if idx < 0 or idx >= len(sentences):
                errors.append(f"句 {idx}: i 超出句序范围（0..{len(sentences) - 1}）。")
            else:
                body = _sentence_body(sentences[idx])
                if zh and zh not in body:
                    errors.append(f"句 {idx}: zh 不在原句正文中（zh={zh}）。")

    if bad_placeholder:
        errors.append(
            "检测到占位符标注（termN/[term]），句序号: "
            f"{bad_placeholder[:20]}{'...' if len(bad_placeholder) > 20 else ''}"
        )

    dup_en = [k for k, v in Counter(en_tokens).items() if k and v > 1]
    if dup_en:
        errors.append(
            "检测到重复 en（会被去重导致覆盖率损失）: "
            f"{dup_en[:20]}{'...' if len(dup_en) > 20 else ''}"
        )

    if suspicious_cut:
        warnings.append(
            "检测到可能截断的 zh 结尾（启发式）句序号: "
            f"{suspicious_cut[:20]}{'...' if len(suspicious_cut) > 20 else ''}"
        )

    return errors, warnings
