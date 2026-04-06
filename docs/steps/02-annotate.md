# 第 2 步：词汇标注（四六级向）

## `system_prompt`（单一来源）

发给模型的完整说明（角色、选词密度、JSON 输出约束）在 **[`util/prompts/chat_annotate_system.txt`](../../util/prompts/chat_annotate_system.txt)**。  
`export-chat-bundle` 导出的 `system_prompt` 字段即该文件全文；修改标注规则时**只改此文件**即可。

## 产出文件

1. **`llm-chat-bundle.json`**（可选，便于复制给模型）  
   `python3 workflow/mingox.py export-chat-bundle --slug <slug>`  
   内含 `system_prompt`、`sentences`（按 `。！？；` 切句后的序号与原文）。

2. **`llm_annotations.json`**（**`build` 必填**）  
   默认路径：`content/drafts/<slug>/llm_annotations.json`，也可用 `meta.json` 的 **`llm_annotations_file`** 指定文件名。须由大模型按本步约定写出；无此文件时 `mingox build` 会失败。

合法 JSON 示例（注意**不要**尾随逗号）：

```json
{
  "version": 1,
  "annotations": [
    { "i": 0, "skip": true },
    {
      "i": 4,
      "zh": "营收",
      "en": "revenue",
      "ipa": "[ˈrevənjuː]",
      "pos": "n.",
      "gloss": "营收"
    }
  ]
}
```

- **`i`**：与 bundle 里 `sentences[].i` 一致（从 0 起）。  
- 无合适词：`{"i": k, "skip": true}`。  
- 有标注：`zh` 须为该句去掉句末 `。！？；` 后正文中的**连续子串**，且与 `en` **同一义项**；`en` 为**单个**英文词位（ASCII 字母数字，无空格、无连字符拼接；专名如 `CUDA`、`AI` 可）；无法用一词对译时请收窄 `zh` 或填 `skip`；`ipa` 用方括号；`pos`、`gloss` 同上例。  
- 合并层会按顺序对 **`en` 去重**，重复的后续条目不生效，尽量少重复。

## zh 与 en 对齐（硬性，流程内须遵守）

**原则**：`en` 所指的就是 `zh` 这一个（或不可分割的术语整体）；**禁止**把「修饰语 + 中心词」整段标成 `zh`，却只给一个只对应中心词的 `en`。

| 错误 | 应改为（示例） |
|------|----------------|
| `zh`「规模化制造」+ `en`「manufacturing」 | `zh`「制造」+ `en`「manufacturing」 |
| `zh`「智慧文明」+ `en`「civilization」 | `zh`「文明」+ `en`「civilization」；若句中需教「智慧」则另条 `zh`「智慧」+ `en`「wisdom」 |
| `zh`「经济意义」+ `en`「economic」 | `zh`「经济」+ `en`「economic」；或改 `en` 与「意义」义项一致 |
| `zh`「边际成本」+ `en`「marginal」 | `zh`「边际」+ `en`「marginal」或 `zh`「成本」+ `en`「cost」等，与英文义项一致的一侧 |

**自检**：念一遍「这句里的 `zh` 是不是正好等于这个英文 headword 在汉语里该指的那一个词？」若否，收窄 `zh` 或换 `en`/`skip`。

**词表路径**（[`workflow/bundle_lexicon_annotate.py`](../../workflow/bundle_lexicon_annotate.py) + TSV）：每一行 `zh<TAB>en<...>` 也必须满足上表；`zh` 取**最小**可匹配子串。详细措辞与反例见 **[`util/prompts/chat_annotate_system.txt`](../../util/prompts/chat_annotate_system.txt)**。

## 与 `build` 衔接

```bash
python3 workflow/mingox.py export-chat-bundle --slug my-topic
# 将 system_prompt + sentences 交给任意大模型 → 保存 llm_annotations.json
python3 workflow/mingox.py build --slug my-topic
```

## 合并规则与密度

标注由大模型按 `chat_annotate_system.txt` 控制选词密度。若成稿 `word-block` 偏少，先改该文件的密度/过滤说明，再 **`export-chat-bundle`** 并让模型**重写** `llm_annotations.json` 后 `build`（改提示词不会自动更新已有 JSON）。合并层 [`util/annotate_merge.py`](../../util/annotate_merge.py) 对同一 `en` **按顺序只保留首次**（与上表「去重」一致）；`en` 须通过 `en_headword_token_ok`（单英文词位等）。

## 标准流程（唯一支持路径）

1. `python3 workflow/mingox.py export-chat-bundle --slug <slug>`  
2. 将 `llm-chat-bundle.json` 中的 `system_prompt` 与 `sentences` 交给大模型，按 JSON 约定写出标注。  
3. 保存为 `content/drafts/<slug>/llm_annotations.json`（或 `meta.llm_annotations_file` 所指路径）。  
4. `python3 workflow/mingox.py build --slug <slug>`

无对话式 API 时，仍可由助手在对话中策展 **TSV 词表**（最长子串匹配 + 全局 `en` 去重），一键覆盖 `llm_annotations.json`：

```bash
python3 workflow/bundle_lexicon_annotate.py --slug <slug>
# 默认 lexicon：util/lexicons/space_datacenter_dense.tsv（偏太空算力题材）
# 其它题材：--lexicon path/to/your.tsv（列：zh<TAB>en<TAB>ipa<TAB>pos<TAB>gloss）
```

然后再 `mingox build`。这与「按 `chat_annotate_system.txt` 自由选词」的大模型路径不同，词表需随稿维护。

**实现**：[`util/annotate_merge.py`](../../util/annotate_merge.py)（启动时加载上述 `txt` 为 `CHAT_SYSTEM_PROMPT`，以及 `apply_annotations_payload`）。

**下一步**：[03-html.md](./03-html.md)。
