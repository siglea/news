#!/usr/bin/env python3
"""
将 kaoyan_vocab_tab.txt 和 kaoyan_vocab_md.md 合并进 vocab_merged.tsv。

用法:
    python3 util/merge_lexicons.py [--top-n 3000] [--dry-run]

策略：
  - 白名单：考研词表中的词，只要不命中黑名单就保留
  - 黑名单：top_n_list 常用词 + 功能词词性 + zh<2字
  - 原始 TSV 也参与过滤，统一标准
"""

import argparse
import re
from pathlib import Path

import eng_to_ipa as ipa_lib
from wordfreq import top_n_list, zipf_frequency

LEXICONS = Path(__file__).parent
TSV_PATH = LEXICONS / "vocab_merged.tsv"
SRC_7E = LEXICONS / "kaoyan_vocab_tab.txt"
SRC_DW = LEXICONS / "kaoyan_vocab_md.md"

POS_RE = re.compile(r"\b(n|v|adj|adv|prep|conj|pron|det|interjection|vt|vi|num|art)\.")

FILTER_POS = {"pron.", "art.", "interjection.", "conj.", "det.", "num."}


def parse_kaoyan_tab(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        en = parts[0].strip().lower()
        raw = parts[1].strip()
        if not en or not raw:
            continue
        if en in out:
            continue
        pos, gloss = _split_pos_gloss(raw)
        if gloss:
            out[en] = {"en": en, "pos": pos, "gloss": gloss}
    return out


def parse_kaoyan_md(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    pat = re.compile(r"^-\s+\*\*(.+?)\*\*\s*[—–-]+\s*(.+)$")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        en = m.group(1).strip().lower()
        raw = m.group(2).strip().rstrip("<")
        if not en or not raw:
            continue
        if en in out:
            continue
        pos, gloss = _split_pos_gloss(raw)
        if gloss:
            out[en] = {"en": en, "pos": pos, "gloss": gloss}
    return out


def _split_pos_gloss(raw: str) -> tuple[str, str]:
    m = POS_RE.search(raw)
    if not m:
        gloss = _clean_gloss(raw)
        return ("n.", gloss)
    pos = m.group(0)
    after = raw[m.end():].strip()
    next_pos = POS_RE.search(after)
    if next_pos:
        gloss = after[:next_pos.start()].strip().rstrip(";；,，")
    else:
        gloss = after
    return (pos, _clean_gloss(gloss))


def _clean_gloss(g: str) -> str:
    g = g.strip().rstrip(";；,，")
    g = re.sub(r"[<>A]", "", g).strip()
    return g


def extract_zh(gloss: str) -> str:
    """从 gloss 提取短中文词（2-4字最佳）用于句内子串匹配。"""
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
    if not candidates:
        return ""
    candidates.sort(key=len)
    return candidates[0]


def get_ipa(en: str) -> str:
    try:
        result = ipa_lib.convert(en)
    except Exception:
        return ""
    if not result or "*" in result:
        return ""
    return f"[{result}]"


def load_existing_tsv(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) == 5:
            out.append({
                "zh": parts[0], "en": parts[1],
                "ipa": parts[2], "pos": parts[3], "gloss": parts[4],
            })
    return out


def build_blacklist(n: int) -> set[str]:
    """用 wordfreq top-N 英语词作为黑名单。"""
    return set(w.lower() for w in top_n_list("en", n))


def is_blocked(en: str, pos: str, blacklist: set) -> str:
    """返回过滤原因，空串表示通过。"""
    if en in blacklist:
        return "top-N"
    if pos in FILTER_POS:
        return "pos"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-n", type=int, default=3000,
                    help="wordfreq top-N 黑名单大小")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    blacklist = build_blacklist(args.top_n)
    print(f"blacklist: top-{args.top_n} = {len(blacklist)} words")

    # --- 加载三个来源 ---
    existing = load_existing_tsv(TSV_PATH)
    print(f"existing TSV: {len(existing)} entries")

    src7 = parse_kaoyan_tab(SRC_7E)
    srcd = parse_kaoyan_md(SRC_DW)
    print(f"kaoyan_tab: {len(src7)} unique en")
    print(f"kaoyan_md: {len(srcd)} unique en")

    # --- 合并所有来源，按 en 去重（原始 TSV 优先保留 zh/ipa） ---
    pool: dict[str, dict] = {}

    for e in existing:
        en = e["en"].lower()
        if en not in pool:
            pool[en] = e

    for en, entry in src7.items():
        if en not in pool:
            pool[en] = entry

    for en, entry in srcd.items():
        if en not in pool:
            pool[en] = entry

    print(f"merged pool (unique en): {len(pool)}")

    # --- 黑名单过滤（统一标准，原始 TSV 也过滤） ---
    kept: dict[str, dict] = {}
    stats = {"top-N": 0, "pos": 0, "no_zh": 0, "no_ipa": 0, "kept": 0}

    for en, entry in pool.items():
        pos = entry.get("pos", "n.")
        reason = is_blocked(en, pos, blacklist)
        if reason:
            stats[reason] = stats.get(reason, 0) + 1
            continue

        has_zh = entry.get("zh")
        has_ipa = entry.get("ipa")

        if has_zh and has_ipa:
            if len(has_zh) < 2:
                stats["no_zh"] += 1
                continue
            kept[en] = entry
            stats["kept"] += 1
            continue

        zh = has_zh or extract_zh(entry.get("gloss", ""))
        if not zh or len(zh) < 2:
            stats["no_zh"] += 1
            continue

        ipa_str = has_ipa or get_ipa(en)
        if not ipa_str:
            stats["no_ipa"] += 1
            continue

        kept[en] = {
            "zh": zh, "en": en, "ipa": ipa_str,
            "pos": pos, "gloss": entry.get("gloss", zh),
        }
        stats["kept"] += 1

    print(f"filter stats: {stats}")

    # --- 按 zh 长度降序排列 ---
    final = sorted(kept.values(), key=lambda x: len(x["zh"]), reverse=True)

    if args.dry_run:
        print(f"\n[dry-run] total would be: {len(final)}")
        # 验证边界词
        check_words = ["hers", "fog", "time", "think", "way",
                       "significant", "additional", "positive",
                       "cascade", "paradox", "ingenious", "loss", "key"]
        print("\n[dry-run] 边界词检查:")
        for w in check_words:
            in_bl = w in blacklist
            in_kept = w in kept
            z = zipf_frequency(w, "en")
            status = "KEPT" if in_kept else "FILTERED"
            reason = f"blacklist={in_bl}" if not in_kept else ""
            print(f"  {w:15s} zipf={z:.2f}  {status:8s}  {reason}")
        return

    lines = [f"{e['zh']}\t{e['en']}\t{e['ipa']}\t{e['pos']}\t{e['gloss']}"
             for e in final]
    TSV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {TSV_PATH}: {len(final)} entries")


if __name__ == "__main__":
    main()
