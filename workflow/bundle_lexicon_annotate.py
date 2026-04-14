#!/usr/bin/env python3
"""
从 llm-chat-bundle.json 用「最长中文子串匹配 + 全局 en 去首」填充 llm_annotations.json。
词表每行须保证 `zh` 与 `en` 义项一一对应（`zh` 取最小可匹配子串，见 chat_annotate_system.txt）。
供本地/Cursor 无 API 时由词表（人工/助手策展）拉高句覆盖率；非 mingox 默认子命令。

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


def _normalize_entry(zh: str, en: str, ipa: str, pos: str, gloss: str) -> dict[str, str] | None:
    zh = zh.strip()
    en = en.strip()
    ipa = ipa.strip()
    pos = pos.strip()
    gloss = gloss.strip()
    if len(zh) < 1 or not en_headword_token_ok(en):
        return None
    if not ipa or not pos or not gloss:
        return None
    if not ipa.startswith("["):
        ipa = f"[{ipa.strip('[]')}]"
    return {"zh": zh, "en": en, "ipa": ipa, "pos": pos, "gloss": gloss}


def _load_lexicon_tsv(path: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        e = _normalize_entry(*parts)
        if e:
            out.append(e)
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
    out: list[dict[str, str]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        row = _normalize_entry(
            str(e.get("zh", "")),
            str(e.get("en", "")),
            str(e.get("ipa", "")),
            str(e.get("pos", "")),
            str(e.get("gloss", "")),
        )
        if row:
            out.append(row)
    out.sort(key=lambda x: len(x["zh"]), reverse=True)
    return out


def _has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _unique_en_token(base_en: str, used: set[str]) -> str:
    token = base_en
    idx = 2
    while token.lower() in used:
        token = f"{base_en}{idx}"
        idx += 1
    return token


def fill_from_bundle(
    bundle_path: Path,
    lex_entries: list[dict[str, str]],
    *,
    suffix_repeated_en: bool = False,
) -> dict:
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    sents = data.get("sentences") or []
    ordered = sorted((int(x["i"]), str(x.get("text", ""))) for x in sents if isinstance(x, dict) and "i" in x)
    lex_sorted = sorted(lex_entries, key=lambda e: len(e["zh"]), reverse=True)
    used_en: set[str] = set()
    annotations: list[dict] = []
    for i, text in ordered:
        body, _ = sentence_body_and_punct(text.replace("\r", ""))
        if not body.strip() or not _has_cjk(body):
            annotations.append({"i": i, "skip": True})
            continue
        pick: dict[str, str] | None = None
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
    ap = argparse.ArgumentParser(description="Fill llm_annotations.json from bundle + lexicon module.")
    ap.add_argument("--slug", required=True)
    ap.add_argument(
        "--lexicon",
        type=Path,
        help="Lexicon: .tsv (zh<TAB>en<TAB>ipa<TAB>pos<TAB>gloss) or .py with ENTRIES. "
        "Default: util/lexicons/space_datacenter_dense.tsv",
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
        help="Allow repeated headwords by appending numeric suffix for dedupe key, e.g. market2.",
    )
    a = ap.parse_args()
    draft = ROOT / "content" / "drafts" / a.slug
    bundle = draft / "llm-chat-bundle.json"
    if not bundle.is_file():
        raise SystemExit(f"missing {bundle}")
    lex_path = a.lexicon or (UTIL / "lexicons" / "space_datacenter_dense.tsv")
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
