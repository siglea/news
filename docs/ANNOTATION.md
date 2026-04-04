# 标注环节总览

从「我要标一篇」到成稿 HTML：**选引擎 → 准备真源文件 → `build` + 校验 + 人工对照根目录 README**。

**第 2 步分册**（概念边界、与 HTML 成稿的关系）：**[docs/steps/02-annotate.md](./steps/02-annotate.md)**。  
**权威规范**：版式、词汇、句密度、相邻块、外源版权块等以仓库根目录 **[README.md](../README.md)** 为准。  
**流水线总览**：[PIPELINE.md](./PIPELINE.md)；**四步索引**：[docs/steps/README.md](./steps/README.md)。  
**同位锚定 / `gloss` / 对话 JSON 字段**：细则见 **[content/drafts/README.md](../content/drafts/README.md)**。

---

## 三步走

1. **选引擎**（见下节决策树），在 `content/drafts/<slug>/meta.json` 写 `annotate_engine` 及所需字段。**默认新稿**用 **`chat_json`**。  
2. **准备真源**：**`chat_json`**：`export-chat-bundle` → 对话产出 `llm_annotations.json`；**`keywords`**：使用 [util/keyword_lexicon.py](../util/keyword_lexicon.py)（经 `annotate_lib` 暴露为 `KEYWORDS`）。  
3. **`python3 workflow/mingox.py build --slug <slug>`** → 生成 `02-annotate-tasks.json` 与 `posts/*.html`；再 **`python3 workflow/mingox.py validate`**（相邻块硬门禁 + 可选密度**仅警告**）。

---

## 引擎选型决策树

| 你的目标 | `annotate_engine` | 渲染真源（唯一） | 说明 |
|----------|-------------------|------------------|------|
| **默认新稿：对话/模型选词**（**推荐**） | **`chat_json`** | **`llm_annotations.json`**（`llm_annotations_file` 可改） | `export-chat-bundle` → 对话产出 JSON → `build`；经 `util/annotate_merge.py` 校验。同位锚定易有偏差时**二轮对话**或对照根 README 修 `llm_annotations.json`。 |
| **快速、仅匹配内置术语表** | 省略或 **`keywords`** | 无单独文件，词表来自 [util/keyword_lexicon.py](../util/keyword_lexicon.py) | 成稿词汇表可能偏短；要补标需在 `_KEYWORD_ENTRIES` 增补后再 `build`。 |

### 禁区（避免双源混用）

- **`chat_json`**：渲染真源仅为 `llm_annotations.json`（及 `llm_annotations_file` 所指路径）。  
- 改引擎时核对 `meta.json`，避免「文件已换、引擎未改」或反之。

---

## 机器校验 vs 编辑规范（分层）

| 类型 | 内容 | 行为 |
|------|------|------|
| **硬门禁** | 相邻 `word-block`（`</span></span>` 与下一 `<span class="word-block"` 之间仅有空白） | `build` 默认执行；失败则 **exit 1**。`--skip-validate` 仅调试用。 |
| **启发式警告** | 每 `<p>` 内「句数」与 `word-block` 数量对比（**近似** README 的 `。！？；` 断句；英文段可粗算 `;`） | `mingox validate` 打印 **WARN**，**不失败**。若整篇 `post-content` 内**没有任何** `word-block`（如非词汇向正文），**不运行**该启发式以免刷屏。详见 [workflow/validate.py](../workflow/validate.py) 与 `workflow/test_validate_density.py`。 |
| **编辑规范** | 每「句」至少一处标注、不识别词清单、同位锚定、`logistics`/固定搭配、`title-en`、版权块不加标等 | **无自动门禁**；`build` 通过 ≠ 全文符合 README，需人工通读或对照范文。 |

---

## 常用命令

```bash
# 对话路径：导出 bundle → 对话生成 JSON → build
python3 workflow/mingox.py export-chat-bundle --slug my-topic
python3 workflow/mingox.py build --slug my-topic

# 全站相邻检测 + 密度警告
python3 workflow/mingox.py validate

# 单篇
python3 workflow/mingox.py validate --post posts/2026-03-29-china-g7-europe-market.html
```

---

## 与 `build_draft.py` 对齐

实现以 [workflow/build_draft.py](../workflow/build_draft.py) 为准：仅识别 **`keywords` / `chat_json`**；旧值 `llm` 已废弃，会提示改用 `chat_json`。
