#!/usr/bin/env python3
"""
Synth llm_annotations.json for chat_json from:
  1) content/drafts/<slug>/01-source.md  (required)
  2) content/drafts/<slug>/annotate_lexicon_extra.json  (optional) — 与本篇正文配套的补充词条
  3) util/keyword_lexicon 全局 KEYWORDS

合并后按句 longest-zh + leftmost 匹配，全文 en 小写去重。不写死在脚本里的 slug。

注意：本脚本为 **keywords 式稀疏占位**，**不是** chat_json 终稿标准（与 EDITORIAL「每句一标」冲突）。终稿须 export-chat-bundle → 对话 LLM；应急词表铺词见 `gen_dense_chat_json.py`（无匹配则 skip）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_UTIL = _ROOT / "util"
if str(_UTIL) not in sys.path:
    sys.path.insert(0, str(_UTIL))

import annotate_lib as al
from annotate_merge import en_headword_token_ok, flatten_paragraphs
from md_split import paragraphs_from_markdown

ROOT = _ROOT
_EXTRA_JSON_NAME = "annotate_lexicon_extra.json"


def _load_extra_entries(draft: Path) -> list[tuple[str, str, str, str, str]]:
    p = draft / _EXTRA_JSON_NAME
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("entries")
    if not isinstance(raw, list):
        return []
    out: list[tuple[str, str, str, str, str]] = []
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        zh = str(row.get("zh", "")).strip()
        en = str(row.get("en", "")).strip()
        ipa = str(row.get("ipa", "")).strip()
        pos = str(row.get("pos", "")).strip()
        gloss = str(row.get("gloss", "")).strip()
        if not zh or not en or not ipa or not pos or not gloss:
            raise ValueError(f"{p}: entries[{i}] missing zh/en/ipa/pos/gloss")
        if not en_headword_token_ok(en):
            raise ValueError(f"{p}: entries[{i}] invalid en={en!r}")
        out.append((zh, en, ipa, pos, gloss))
    return out


def _merged_entries(draft: Path) -> list[tuple[str, str, str, str, str]]:
    extra = _load_extra_entries(draft)
    merged = extra + list(al.KEYWORDS)
    merged.sort(key=lambda x: len(x[0]), reverse=True)
    return merged


def _pick_unused(body: str, used_en: set[str], entries: list[tuple[str, str, str, str, str]]):
    best: tuple[int, int, str, str, str, str, str] | None = None
    for zh, en, ipa, pos, gloss in entries:
        if en.lower() in used_en:
            continue
        idx = body.find(zh)
        if idx < 0:
            continue
        cand = (-len(zh), idx, zh, en, ipa, pos, gloss)
        if best is None or cand < best:
            best = cand
    if best is None:
        return None
    _, _, zh, en, ipa, pos, gloss = best
    return zh, en, ipa, pos, gloss


def run_synth_lexicon_annotations(slug: str) -> None:
    draft = ROOT / "content" / "drafts" / slug
    src = draft / "01-source.md"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    entries = _merged_entries(draft)
    paras = paragraphs_from_markdown(src.read_text(encoding="utf-8"))
    sents, _ = flatten_paragraphs(paras)
    used_en: set[str] = set()
    ann: list[dict] = []
    for i, sent in enumerate(sents):
        body, _ = al.sentence_body_and_punct(sent)
        if not body.strip():
            ann.append({"i": i, "skip": True})
            continue
        pk = _pick_unused(body, used_en, entries)
        if not pk:
            ann.append({"i": i, "skip": True})
            continue
        zh, en, ipa, pos, gloss = pk
        if not ipa.startswith("["):
            ipa = f"[{ipa.strip('[]')}]"
        used_en.add(en.lower())
        ann.append({"i": i, "zh": zh, "en": en, "ipa": ipa, "pos": pos, "gloss": gloss})
    out = {"version": 1, "annotations": ann}
    out_path = draft / "llm_annotations.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_ok = sum(1 for a in ann if not a.get("skip"))
    extra_note = f" + {_EXTRA_JSON_NAME}" if (draft / _EXTRA_JSON_NAME).is_file() else ""
    print("wrote", out_path, f"annotated {n_ok}/{len(ann)} sentences", f"(01-source.md{extra_note} + global lexicon)")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: synth_llm_annotations_lexicon.py <slug>")
    run_synth_lexicon_annotations(sys.argv[1])


if __name__ == "__main__":
    main()
