#!/usr/bin/env python3
"""
将 kaoyan_vocab_tab.txt 和 kaoyan_vocab_md.md 合并进 vocab_merged.tsv。

用法:
    python3 util/lexicons/merge_lexicons.py [--top-n 3000] [--dry-run]

输出格式（每行 3 列 TSV）:
    en<TAB>ipa<TAB>definition

definition 示例: n. 垃圾；废物 ｜v. 丢弃；修剪树枝

每个 en 只有一行，多词性用 ｜ 分隔。消费端从 definition 动态提取 zh 做匹配。
"""

import argparse
import re
from pathlib import Path

import eng_to_ipa as ipa_lib
from wordfreq import top_n_list

LEXICONS = Path(__file__).parent
TSV_PATH = LEXICONS / "vocab_merged.tsv"
SRC_7E = LEXICONS / "kaoyan_vocab_tab.txt"
SRC_DW = LEXICONS / "kaoyan_vocab_md.md"

POS_RE = re.compile(r"\b(n|v|adj|adv|prep|conj|pron|det|interjection|vt|vi|num|art)\.")

FILTER_POS_ONLY = {"pron.", "art.", "interjection.", "conj.", "det.", "num."}


def _split_all_pos_gloss(raw: str) -> list:
    """从 'n. 反抗；造反 v. 起义' 拆出所有 (pos, gloss) 对。"""
    matches = list(POS_RE.finditer(raw))
    if not matches:
        gloss = _clean_gloss(raw)
        return [("n.", gloss)] if gloss else []
    results = []
    for idx, m in enumerate(matches):
        pos = m.group(0)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        gloss = _clean_gloss(raw[start:end])
        if gloss:
            results.append((pos, gloss))
    return results


def parse_kaoyan_tab(path: Path) -> dict:
    out = {}
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
        pairs = _split_all_pos_gloss(raw)
        if pairs:
            out[en] = pairs
    return out


def parse_kaoyan_md(path: Path) -> dict:
    out = {}
    pat = re.compile(r"^-\s+\*\*(.+?)\*\*\s*[—–-]+\s*(.+)$")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        en = m.group(1).strip().lower()
        raw = m.group(2).strip().rstrip("<")
        if not en or not raw:
            continue
        pairs = _split_all_pos_gloss(raw)
        if not pairs:
            continue
        if en not in out:
            out[en] = []
        existing_pos = {p for p, _ in out[en]}
        for pos, gloss in pairs:
            if pos not in existing_pos:
                out[en].append((pos, gloss))
                existing_pos.add(pos)
    return out


def _clean_gloss(g: str) -> str:
    g = g.strip().rstrip(";；,，")
    g = re.sub(r"[<>A]", "", g).strip()
    return g


def _has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _build_definition(pairs: list) -> str:
    """将 [(pos, gloss), ...] 合并为 'n. 垃圾；废物 ｜v. 丢弃' 格式。
    同时归一化冗余词性（v./vt./vi. 有重叠时合并）。"""
    if not pairs:
        return ""
    # 归一化：vt./vi. 如果 v. 也存在就丢弃
    pos_set = {p for p, _ in pairs}
    if "v." in pos_set:
        pairs = [(p, g) for p, g in pairs if p not in ("vt.", "vi.")]

    seen = set()
    parts = []
    for pos, gloss in pairs:
        if pos in seen:
            continue
        seen.add(pos)
        if pos in FILTER_POS_ONLY:
            continue
        parts.append(f"{pos} {gloss}")
    return " ｜".join(parts)


def get_ipa(en: str) -> str:
    try:
        result = ipa_lib.convert(en)
    except Exception:
        return ""
    if not result or "*" in result:
        return ""
    return f"[{result}]"


def load_existing_tsv(path: Path) -> dict:
    """加载已有 TSV（兼容旧 5 列和新 3 列），返回 {en: {ipa, definition}}。"""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            en, ipa, definition = parts
            en = en.strip().lower()
            if en and en not in out:
                out[en] = {"ipa": ipa.strip(), "definition": definition.strip()}
        elif len(parts) == 5:
            col0 = parts[0]
            if re.search(r"[\u4e00-\u9fff]", col0):
                _, en, ipa, pos, gloss = parts
            else:
                en, ipa, pos, _, gloss = parts
            en = en.strip().lower()
            if en not in out:
                out[en] = {"ipa": ipa.strip(), "definition": f"{pos.strip()} {gloss.strip()}"}
            else:
                old_def = out[en]["definition"]
                new_part = f"{pos.strip()} {gloss.strip()}"
                if new_part not in old_def:
                    out[en]["definition"] = f"{old_def} ｜{new_part}"
    return out


def build_blacklist(n: int) -> set:
    return set(w.lower() for w in top_n_list("en", n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-n", type=int, default=3000,
                    help="wordfreq top-N 黑名单大小")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    blacklist = build_blacklist(args.top_n)
    print(f"blacklist: top-{args.top_n} = {len(blacklist)} words")

    existing = load_existing_tsv(TSV_PATH)
    print(f"existing TSV: {len(existing)} entries")

    src7 = parse_kaoyan_tab(SRC_7E)
    srcd = parse_kaoyan_md(SRC_DW)
    print(f"kaoyan_tab: {len(src7)} unique en")
    print(f"kaoyan_md: {len(srcd)} unique en")

    # --- 合并所有来源，按 en 合并 ---
    # pool: en -> {ipa, pairs: list[(pos, gloss)]}
    pool = {}

    for en, info in existing.items():
        pool[en] = {"ipa": info["ipa"], "definition": info["definition"]}

    # 考研词表：有结构化 n./v. 分段的，始终用其生成 definition（覆盖旧 TSV 里错误的 n./v. 单行合并）
    ipa_cache = {}
    for en in set(list(src7.keys()) + list(srcd.keys())):
        pairs_7 = src7.get(en, [])
        pairs_d = srcd.get(en, [])
        all_pairs = []
        seen_pos = set()
        for pos, gloss in pairs_7 + pairs_d:
            if pos not in seen_pos:
                all_pairs.append((pos, gloss))
                seen_pos.add(pos)

        definition = _build_definition(all_pairs)
        if not definition or not _has_cjk(definition):
            continue
        if en in pool:
            pool[en]["definition"] = definition
        else:
            pool[en] = {"ipa": "", "definition": definition}

    print(f"merged pool: {len(pool)} unique en")

    # --- 黑名单过滤 + 补 IPA ---
    final = []
    stats = {"top-N": 0, "no_cjk": 0, "no_ipa": 0, "kept": 0}

    for en, info in pool.items():
        if en in blacklist:
            stats["top-N"] += 1
            continue
        if not _has_cjk(info["definition"]):
            stats["no_cjk"] += 1
            continue

        ipa_str = info["ipa"]
        if not ipa_str:
            if en not in ipa_cache:
                ipa_cache[en] = get_ipa(en)
            ipa_str = ipa_cache[en]
        if not ipa_str:
            stats["no_ipa"] += 1
            continue
        if not ipa_str.startswith("["):
            ipa_str = f"[{ipa_str.strip('[]')}]"

        final.append({"en": en, "ipa": ipa_str, "definition": info["definition"]})
        stats["kept"] += 1

    print(f"filter stats: {stats}")

    final.sort(key=lambda x: x["en"])

    if args.dry_run:
        print(f"\n[dry-run] total: {len(final)} entries")
        check = ["alarm", "revolt", "neglect", "pose", "fuse", "cascade", "bias", "trash"]
        print("\n[dry-run] 示例:")
        for w in check:
            hits = [e for e in final if e["en"] == w]
            for h in hits:
                print(f"  {h['en']:12s} {h['ipa']:16s} {h['definition'][:60]}")
            if not hits:
                print(f"  {w:12s} (not found)")
        return

    lines = [f"{e['en']}\t{e['ipa']}\t{e['definition']}" for e in final]
    TSV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {TSV_PATH}: {len(final)} entries")


if __name__ == "__main__":
    main()
