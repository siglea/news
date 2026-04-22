#!/usr/bin/env python3
"""
标注 JSON 质量门禁。build 时必跑；亦可用 `mingox validate --annotations` 对全部草稿全量检查。

为规避「假头词漏网」采用多层规则：
- 原样 en：term*、lex*、*zh 尾缀、常见占位 token；
- 与合并层一致：去掉 en 尾部分数字后若词干为 lex/term 等，仍判无效（与 annotate_merge 的展示去重一致）。
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# 与 util/annotate_merge.py normalize_annotation_item 中 en_display 的 strip 规则一致
_EN_STRIP_TRAILING_DIGITS = re.compile(r"\d+$")
_RE_PLACEHOLDER_TERM = re.compile(r"^term\d*$", re.IGNORECASE)
_RE_PLACEHOLDER_LEX = re.compile(r"^lex(\d+.*)?$", re.IGNORECASE)
# 将「英文」与 zh 等标记拼在 token 上（如 screeningzh）
_SUS_EN_SUFFIX_ZH = re.compile(r"(?i)^[A-Za-z0-9.]{4,}zh\d*$")
# 显式空桩/流程占位
_TEMPLATED_TOKENS = re.compile(
    r"(?i)^(tbd|todo|fixme|xxx|tmp|temp|placeholder|pending)\d*$"
)
# 经合并展示层去尾数后，不得仅为下列词干（与 annotate_merge 一致）
_FORBIDDEN_STEMS = frozenset(
    s.lower() for s in ("lex", "term", "tbd", "tmp", "temp", "todo", "fixme", "xxx")
)
# 历史成稿、口语化「假词」、禁止连写的复合词
_EXPLICIT_FAKE = re.compile(
    r"(?i)^(howcome|wherefore|failurerate|siliconworld|linearthinking|"
    r"postalphafold\w*|smallmolecule\w*)$"
)
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


def _en_stem_after_trailing_digits(en: str) -> str:
    e = en.strip()
    s = _EN_STRIP_TRAILING_DIGITS.sub("", e).strip() or e
    return s.lower()


def en_suspect_placeholder_or_fake(en: str) -> bool:
    """en 为占位、假头词、或经合并后展示为 lex/term 等无效词时返回 True。"""
    e = en.strip()
    if not e:
        return False
    if _RE_PLACEHOLDER_TERM.fullmatch(e) or _RE_PLACEHOLDER_LEX.fullmatch(e):
        return True
    if _SUS_EN_SUFFIX_ZH.fullmatch(e):
        return True
    if _TEMPLATED_TOKENS.match(e):
        return True
    if _EXPLICIT_FAKE.match(e):
        return True
    if _en_stem_after_trailing_digits(e) in _FORBIDDEN_STEMS:
        return True
    return False


def check_quality(
    meta: dict[str, Any],
    payload: dict[str, Any],
    *,
    sentences: list[str] | None = None,
    require_meta: bool = True,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if require_meta:
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

        if en_suspect_placeholder_or_fake(en) or ipa.lower().strip("[]") == "term":
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
            "检测到无效/占位 en（term*、lex*、*zh 尾缀、假词如 howcome，"
            "或去尾数后为 lex/term 等；以及 [term] 音标）。句序号: "
            f"{bad_placeholder[:30]}{'...' if len(bad_placeholder) > 30 else ''}"
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


def _load_draft_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sentences_for_draft(draft_dir: Path) -> list[str] | None:
    b = draft_dir / "llm-chat-bundle.json"
    if not b.is_file():
        return None
    data = _load_draft_json(b)
    sents = data.get("sentences") or []
    try:
        ordered = sorted(
            (int(x["i"]), str(x.get("text", "")))
            for x in sents
            if isinstance(x, dict) and "i" in x
        )
    except (TypeError, ValueError):
        return None
    return [t for _, t in ordered] if ordered else None


def check_draft_annotations_file(
    llm_annotations: Path, *, require_meta: bool = True
) -> tuple[list[str], list[str]]:
    """
    对单篇 `content/drafts/<slug>/llm_annotations.json` 跑与 build 相同的门禁
   （若同目录有 llm-chat-bundle.json 与 meta.json 则一并使用）。
    """
    payload = _load_draft_json(llm_annotations)
    draft = llm_annotations.parent
    meta_p = draft / "meta.json"
    meta: dict = _load_draft_json(meta_p) if meta_p.is_file() else {}
    sents = _sentences_for_draft(draft)
    s_arg = sents if sents else None
    return check_quality(
        meta, payload, sentences=s_arg, require_meta=require_meta
    )


def validate_all_draft_annotations(
    content_drafts: Path,
    *,
    require_meta: bool = True,
    slug: str | None = None,
) -> int:
    """
    扫描 `content/drafts/**/llm_annotations.json`。
    与 `mingox build` 前门禁对齐；全仓库 CI 中建议跑一遍（或只检查 `--slug` 一篇）。
    """
    if slug:
        f = content_drafts / slug / "llm_annotations.json"
        if not f.is_file():
            print(f"missing {f}", file=sys.stderr)
            return 1
        files = [f]
    else:
        files = sorted(content_drafts.glob("*/llm_annotations.json"))
    if not files:
        print(f"no llm_annotations.json under {content_drafts}", file=sys.stderr)
        return 0
    code = 0
    for f in files:
        errs, warns = check_draft_annotations_file(
            f, require_meta=require_meta
        )
        rel = f.relative_to(content_drafts)
        for w in warns:
            print(f"{rel} [warn] {w}", file=sys.stderr)
        if errs:
            code = 1
            print(f"FAIL {rel} ({f}):", file=sys.stderr)
            for e in errs:
                print(f"  {e}", file=sys.stderr)
    if code == 0:
        print(
            f"OK: all {len(files)} llm_annotations.json in {content_drafts} "
            f"(placeholders, dup en, etc.)"
        )
    return code
