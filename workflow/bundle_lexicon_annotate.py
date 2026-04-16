#!/usr/bin/env python3
"""
从 llm-chat-bundle.json 用「最长中文子串匹配 + 全局 en 去首」填充 llm_annotations.json。
词表格式: en<TAB>ipa<TAB>definition (3 列)，definition 示例: n. 垃圾；废物 ｜v. 丢弃
消费端从 definition 动态提取 zh 候选词做匹配并推导 pos/gloss。

示例：
  python3 workflow/bundle_lexicon_annotate.py --slug mp-qsmaket-article
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTIL = ROOT / "util"
sys.path.insert(0, str(UTIL))
from annotate_lib import sentence_body_and_punct  # noqa: E402
from annotate_merge import en_headword_token_ok  # noqa: E402

_POS_RE = re.compile(
    r"\b((?:n|v|adj|adv|prep|conj|pron|det|interjection|vt|vi|num|art)\."
    r"(?:/(?:n|v|adj|adv|vt|vi)\.)*)"
)


def _parse_definition(definition: str) -> list:
    """'n. 垃圾；废物 ｜v. 丢弃' → [('n.', '垃圾；废物'), ('v.', '丢弃')]"""
    sections = re.split(r"\s*｜\s*", definition)
    result = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        m = _POS_RE.match(sec)
        if m:
            pos = m.group(1)
            gloss = sec[m.end():].strip()
        else:
            pos = ""
            gloss = sec
        if gloss:
            result.append((pos, gloss))
    return result


def _extract_zh_candidates(gloss: str) -> list:
    """从 gloss 提取 2-4 字中文词，按长度降序。"""
    cleaned = re.sub(r"[（(].+?[)）]", "", gloss)
    cleaned = re.sub(r"〔.+?〕", "", cleaned)
    cleaned = re.sub(r"…+", "", cleaned)
    parts = re.split(r"[；;，,、]", cleaned)
    candidates = []
    for p in parts:
        p = p.strip()
        p = re.sub(r"^(使|被|把|将|让|给)", "", p)
        cjk_spans = re.findall(r"[\u4e00-\u9fff]{2,4}", p)
        candidates.extend(cjk_spans)
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    unique.sort(key=len, reverse=True)
    return unique


def _load_lexicon_tsv(path: Path) -> list:
    """加载 3 列 TSV，生成扁平 match 列表 [{zh, en, ipa, pos, gloss}, ...]"""
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        en, ipa, definition = parts
        en = en.strip()
        ipa = ipa.strip()
        if not en or not ipa or not en_headword_token_ok(en):
            continue
        if not ipa.startswith("["):
            ipa = f"[{ipa.strip('[]')}]"
        sections = _parse_definition(definition)
        for pos, gloss in sections:
            zh_candidates = _extract_zh_candidates(gloss)
            for zh in zh_candidates:
                out.append({
                    "zh": zh, "en": en, "ipa": ipa,
                    "pos": pos, "gloss": gloss,
                })
    out.sort(key=lambda x: len(x["zh"]), reverse=True)
    return out


def _load_lexicon_module(path: Path):
    spec = importlib.util.spec_from_file_location("annotate_lexicon_mod", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    entries = getattr(mod, "ENTRIES", None)
    if not isinstance(entries, list):
        raise ValueError(f"{path} must define ENTRIES: list[dict]")
    out = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        en = str(e.get("en", "")).strip()
        ipa = str(e.get("ipa", "")).strip()
        pos = str(e.get("pos", "")).strip()
        zh = str(e.get("zh", "")).strip()
        gloss = str(e.get("gloss", "")).strip()
        if not zh or not en_headword_token_ok(en):
            continue
        if not ipa or not pos or not gloss:
            continue
        if not ipa.startswith("["):
            ipa = f"[{ipa.strip('[]')}]"
        out.append({"zh": zh, "en": en, "ipa": ipa, "pos": pos, "gloss": gloss})
    out.sort(key=lambda x: len(x["zh"]), reverse=True)
    return out


def _has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _unique_en_token(base_en: str, used: set) -> str:
    token = base_en
    idx = 2
    while token.lower() in used:
        token = f"{base_en}{idx}"
        idx += 1
    return token


def fill_from_bundle(
    bundle_path: Path,
    lex_entries: list,
    *,
    suffix_repeated_en: bool = False,
) -> dict:
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    sents = data.get("sentences") or []
    ordered = sorted((int(x["i"]), str(x.get("text", ""))) for x in sents if isinstance(x, dict) and "i" in x)
    lex_sorted = sorted(lex_entries, key=lambda e: len(e["zh"]), reverse=True)
    used_en = set()
    annotations = []
    for i, text in ordered:
        body, _ = sentence_body_and_punct(text.replace("\r", ""))
        if not body.strip() or not _has_cjk(body):
            annotations.append({"i": i, "skip": True})
            continue
        pick = None
        for e in lex_sorted:
            en = e["en"]
            if (not suffix_repeated_en) and en.lower() in used_en:
                continue
            if e["zh"] in body:
                pick = e
                break
        if pick:
            out_en = pick["en"]
            if suffix_repeated_en:
                out_en = _unique_en_token(out_en, used_en)
            if out_en.lower() in used_en:
                annotations.append({"i": i, "skip": True})
                continue
            used_en.add(out_en.lower())
            annotations.append(
                {
                    "i": i,
                    "zh": pick["zh"],
                    "en": out_en,
                    "ipa": pick["ipa"],
                    "pos": pick["pos"],
                    "gloss": pick["gloss"],
                }
            )
        else:
            annotations.append({"i": i, "skip": True})
    return {"version": 1, "annotations": annotations}


def main() -> None:
    ap = argparse.ArgumentParser(description="Fill llm_annotations.json from bundle + lexicon.")
    ap.add_argument("--slug", required=True)
    ap.add_argument(
        "--lexicon",
        type=Path,
        help="Lexicon: .tsv (en<TAB>ipa<TAB>definition) or .py with ENTRIES. "
        "Default: util/lexicons/vocab_merged.tsv",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Default: content/drafts/<slug>/llm_annotations.json",
    )
    ap.add_argument(
        "--suffix-repeated-en",
        action="store_true",
        help="Allow repeated headwords by appending numeric suffix.",
    )
    a = ap.parse_args()
    draft = ROOT / "content" / "drafts" / a.slug
    bundle = draft / "llm-chat-bundle.json"
    if not bundle.is_file():
        raise SystemExit(f"missing {bundle}")
    lex_path = a.lexicon or (UTIL / "lexicons" / "vocab_merged.tsv")
    if not lex_path.is_file():
        raise SystemExit(f"missing lexicon {lex_path}")
    if lex_path.suffix.lower() == ".tsv":
        entries = _load_lexicon_tsv(lex_path)
    else:
        entries = _load_lexicon_module(lex_path)
    payload = fill_from_bundle(bundle, entries, suffix_repeated_en=a.suffix_repeated_en)
    out = a.output or (draft / "llm_annotations.json")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n = len(payload["annotations"])
    tagged = sum(1 for x in payload["annotations"] if not x.get("skip"))
    print(f"wrote {out} sentences={n} annotated={tagged} skip={n - tagged}", file=sys.stderr)


if __name__ == "__main__":
    main()
