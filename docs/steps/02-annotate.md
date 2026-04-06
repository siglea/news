# 第 2 步：词汇标注（四六级向）

本步产出 **`llm_annotations.json`**。**没有该文件则 `mingox build` 直接失败**（见 [`workflow/build_draft.py`](../../workflow/build_draft.py)）。成稿中的 `word-block` 与篇末词汇表均依赖此文件经 [`util/annotate_merge.py`](../../util/annotate_merge.py) 合并进段落 HTML。

---

## 1. 规则单一来源（改规则只改这里）

角色、选词密度、JSON 形状、**zh/en 对齐要求**的完整表述在：

**[`util/prompts/chat_annotate_system.txt`](../../util/prompts/chat_annotate_system.txt)**

执行下面「导出 bundle」后，JSON 里的 `system_prompt` 字段即为该文件全文；**不要**在别处复制一份互相漂移的说明。

---

## 2. 产出物说明

| 文件 | 是否必需 | 说明 |
|------|----------|------|
| `llm-chat-bundle.json` | 生成标注**前**强烈建议有 | `export-chat-bundle` 写出，含 `system_prompt` 与按 `。！？；` 切句的 `sentences[]`（每项含句序号 `i` 与 `text`）。 |
| `llm_annotations.json` | **build 必需** | 默认：`content/drafts/<slug>/llm_annotations.json`；也可在 `meta.json` 里用 **`llm_annotations_file`** 改文件名。 |

---

## 3. 推荐主路径：导出 bundle → 对话场景下按 prompt 生成

若当前处于**大模型对话场景**（见 **§4**），推荐用 **`llm-chat-bundle.json`** 做 **prompt 方式**生成 `llm_annotations.json`。典型环境包括 Cursor 内助手、其它能引用仓库文件并多轮对话的 IDE/工具界面；**同一套规则与步骤**，不依赖「必须打开某个外部网站」才算另一条路。**不必**默认跑词表脚本；无对话环境时见 **§5**。

**步骤：**

1. **导出 bundle（与正文句序对齐的唯一依据）**  
   ```bash
   python3 workflow/mingox.py export-chat-bundle --slug <slug>
   ```

2. **在对话场景下，按 prompt 生成 `llm_annotations.json`**（何为对话场景见 **§4**）  
   - 模型或助手读取同一草稿目录下的 `llm-chat-bundle.json`：使用其中的 **`system_prompt`**（即 `chat_annotate_system.txt`）+ **`sentences`**。  
   - 严格按 bundle 中句序，为**每一个** `i` 输出一条对象：有标注则 `zh` / `en` / `ipa` / `pos` / `gloss`，无合适词则 `{"i": k, "skip": true}`。  
   - **遵守下文「zh 与 en 一一对应」**；`en` 须为合法单 token（见合并层 `en_headword_token_ok`：ASCII 字母数字、无空格、无连字符拼接等）。  
   - 句数很多时，可**分块写入**同一 JSON 文件或使用仓库内脚本拼接，避免因单次回复过长截断；**不要**为图省事改用词表敷衍，除非进入 **§5** 兜底场景。  
   - 要求模型**只输出一个合法 JSON 对象**（结构见下文 **§6**），**不要**外层再包 Markdown 代码块，便于直接落盘或粘贴进文件。

3. **构建**  
   ```bash
   python3 workflow/mingox.py build --slug <slug>
   ```

**自检（模型或助手在保存前快速过一遍）：**  
每条非 `skip` 的 `zh` 是否在对应句的**正文**（去掉句末 `。！？；`）里**逐字连续出现**？`en` 是否**只**对应该 `zh`，而不是对一长串里某个未写进 `zh` 的词？

---

## 4. 环境与分支：是否为大模型对话场景

**先判断环境**：你是否能在**同一上下文**里持续用自然语言下达任务，让模型按照 `llm-chat-bundle.json` 中的 **`system_prompt`**（即 `chat_annotate_system.txt` 全文）与 **`sentences`** 的约束，产出符合 **§6** 的 `llm_annotations.json`，并由人或助手写入 `content/drafts/<slug>/`（或等价路径）？

- **若是对话场景**：统一按 **prompt 方式**处理——具体操作见上文 **§3** 第 2、3 步。无论界面是 IDE 内助手、可挂载工作区的对话工具，还是**仅**浏览器里的聊天窗口，只要仍是「在同一对话中按**同一套** bundle 约束生成 JSON」，都属于**同一路径**，**不是**与 prompt 并列的「复制给外部网页才算第二步」的流程。

- **若不是对话场景**（例如只有脚本与终端、当前拿不到任何大模型对话）：使用 **§5** 词表脚本做占位或加速，或自行手写/编辑 `llm_annotations.json`。

规则仍以 **`chat_annotate_system.txt`** 为准；模型输出若违反对齐或 `en` 格式，合并层会丢弃无效条或导致版面异常，需人工修正 JSON。

---

## 5. 兜底路径：词表脚本（非默认）

[`workflow/bundle_lexicon_annotate.py`](../../workflow/bundle_lexicon_annotate.py) 根据 **`llm-chat-bundle.json`** + **TSV 词表**（默认 [`util/lexicons/space_datacenter_dense.tsv`](../../util/lexicons/space_datacenter_dense.tsv)）做最长子串匹配并写 `llm_annotations.json`。

**适用：** 无对话环境、极快占位、或该题材已有维护良好的专用 TSV。  
**不适用作为默认：** 义项与密度通常弱于按 `chat_annotate_system.txt` 自由选词；题材与词表不符时命中率差。  
**TSV 列：** `zh<TAB>en<TAB>ipa<TAB>pos<TAB>gloss`（每行同样须满足 **zh/en 一一对应**，`zh` 取与 `en` 对齐的**最小**子串）。

```bash
python3 workflow/bundle_lexicon_annotate.py --slug <slug>
# 自定义词表：
python3 workflow/bundle_lexicon_annotate.py --slug <slug> --lexicon path/to/your.tsv
```

然后 `mingox build`。

---

## 6. `llm_annotations.json` 形状（合法示例）

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

- **`i`**：与 bundle 中 `sentences[].i` 一致（从 0 起，**每个序号一条**）。  
- **`skip`**：该句没有合格候选时使用。  
- **非 `skip`**：`zh`、`en`、`ipa`、`pos`、`gloss` 均必填且须通过合并层校验（`zh` 在句内、`en` 单 token 等）。

---

## 7. zh 与 en 一一对应（硬性）

**原则：** `en` 所指的就是 **`zh` 这一个词**（或汉语里**不可分割**、且与 `en` 同义的术语整体）。禁止「一长串中文 + 只对应其中一部分词的英文」。

| 错误 | 应改为（示例） |
|------|----------------|
| `zh`「规模化制造」+ `en`「manufacturing」 | `zh`「制造」+ `en`「manufacturing」 |
| `zh`「智慧文明」+ `en`「civilization」 | `zh`「文明」+ `en`「civilization」；若要教「智慧」则用另一句或另条 `zh`「智慧」+ `en`「wisdom」 |
| `zh`「经济意义」+ `en`「economic」 | `zh`「经济」+ `en`「economic」，或改 `en` 与「意义」义项一致 |
| `zh`「边际成本」+ `en`「marginal」 | `zh`「边际」+ `en`「marginal」或 `zh`「成本」+ `en`「cost」等与 `en` **严格对应**的一侧 |

**一句话自检：** 读者能否认为「这个英文词就是在解释我高亮的这几个汉字」？若否，收窄 `zh` 或换 `en`，否则填 `skip`。

Cursor 内编辑标注相关文件时，另见项目规则 **`.cursor/rules/annotate-zh-en-alignment.mdc`**。

---

## 8. 合并层行为与密度

- 实现入口：**[`util/annotate_merge.py`](../../util/annotate_merge.py)**（`apply_annotations_payload`、`rows_from_annotations_payload`、`dedupe_in_order`）。  
- **同一 `en`（大小写不敏感）按句顺序只保留第一次**；后续相同 `en` 的标注在合并结果中视为无效，故提示词要求尽量少重复 `en`。  
- **改 `chat_annotate_system.txt` 不会自动更新已有 `llm_annotations.json`**。要新密度或新规则，须重新导出 bundle 并**重写**标注再 `build`。  
- `build` 时若覆盖率偏低，stderr 可能出现启发式提示；**相邻 `word-block` 校验**见 [`03-html.md`](./03-html.md) 与 `mingox validate`。

---

## 9. 命令速查

```bash
python3 workflow/mingox.py export-chat-bundle --slug <slug>
# 生成并保存 content/drafts/<slug>/llm_annotations.json 后：
python3 workflow/mingox.py build --slug <slug>
python3 workflow/mingox.py validate --post posts/你的成稿.html
```

---

## 10. 下一步

**[03-html.md](./03-html.md)**：`build` 成稿结构、校验与词汇表反扫说明。
