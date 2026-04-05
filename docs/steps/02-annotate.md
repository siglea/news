# 第 2 步：词汇标注（四六级向）

## `system_prompt`（单一来源）

发给模型的完整说明（角色、选词密度、JSON 输出约束）在 **[`util/prompts/chat_annotate_system.txt`](../../util/prompts/chat_annotate_system.txt)**。  
`export-chat-bundle` 导出的 `system_prompt` 字段即该文件全文；修改标注规则时**只改此文件**即可。

## 产出文件

1. **`llm-chat-bundle.json`**（可选，便于复制给模型）  
   `python3 workflow/mingox.py export-chat-bundle --slug <slug>`  
   内含 `system_prompt`、`sentences`（按 `。！？；` 切句后的序号与原文）。

2. **`llm_annotations.json`**（`build` 会读取）  
   默认路径：`content/drafts/<slug>/llm_annotations.json`，也可用 `meta.json` 的 **`llm_annotations_file`** 指定文件名。

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

## 与 `build` 衔接

```bash
python3 workflow/mingox.py export-chat-bundle --slug my-topic
# 将 system_prompt + sentences 交给任意大模型 → 保存 llm_annotations.json
python3 workflow/mingox.py build --slug my-topic
```

无大模型 API 时，可用词表启发式生成稠密草稿（**非** `mingox` 子命令，需自行维护 [`workflow/lexicon_fill_annotations.py`](../../workflow/lexicon_fill_annotations.py) 内词表）：

```bash
python3 workflow/lexicon_fill_annotations.py \
  --bundle content/drafts/<slug>/llm-chat-bundle.json \
  -o content/drafts/<slug>/llm_annotations.json
```

若无 `llm_annotations.json`，`build` 仅生成无 `word-block` 的正文（见 [03-html.md](./03-html.md)）。

**实现**：[`util/annotate_merge.py`](../../util/annotate_merge.py)（启动时加载上述 `txt` 为 `CHAT_SYSTEM_PROMPT`，以及 `apply_annotations_payload`）。

**下一步**：[03-html.md](./03-html.md)。
