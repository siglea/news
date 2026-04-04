# 第 2 步：标注（语义与真源）

本步关注：**选什么引擎、维护哪些文件、语义规则（同位锚定、词表字段）**。  
**不**在本篇展开整页 HTML 壳与 CSS（见 [03-html.md](./03-html.md)）。

---

## 当前实现说明（与 HTML 的关系）

今天 **`mingox build` 一条命令**同时完成：把标注合并进段落 **HTML 片段**（含 `word-block`）→ 再套全页模板写出 `posts/*.html`。  
因此磁盘上的 **`02-annotate-tasks.json`** 里 `paragraphs[].html` 已是「带标签的 `<p>`」，不是中立的纯语义 IR。若未来要「标注只产语义、成稿再渲染」，见 [IR-ROADMAP.md](./IR-ROADMAP.md)。

---

## 权威链接

| 主题 | 文档 |
|------|------|
| 引擎决策树、真源禁区、校验分层 | **[docs/ANNOTATION.md](../ANNOTATION.md)** |
| `zh`/`en` 同位锚定、`gloss`、对话 JSON | **[content/drafts/README.md](../../content/drafts/README.md)** |
| 选取原则、句密度、相邻块（编辑规范全文） | 根目录 **[README.md](../../README.md)**「词汇标注规范」等章节 |

---

## 引擎与文件（速查）

| `meta.annotate_engine` | 真源文件 | 说明 |
|------------------------|----------|------|
| **`chat_json`**（**默认推荐新稿**） | `llm_annotations_file`（默认 `llm_annotations.json`） | 先 `export-chat-bundle`，对话产出 JSON；经 `annotate_merge` 校验 |
| 省略或 `keywords` | 无单独文件（[util/keyword_lexicon.py](../../util/keyword_lexicon.py)） | 快速，词汇表偏短；扩充 `_KEYWORD_ENTRIES` |

**对话路径示例**：

```bash
python3 workflow/mingox.py export-chat-bundle --slug my-topic
# 将 bundle 交给助手 → 保存 llm_annotations.json → meta 设 annotate_engine: chat_json
python3 workflow/mingox.py build --slug my-topic
```

---

## 复合任务快照

`build` 后生成 **`02-annotate-tasks.json`**：`paragraphs[]` 含 `source_text` 与当前实现下的 **`html`（已含标注标签）**，便于 diff 与复查。

---

## 下一步

- 成稿 HTML 结构、版权块、词汇表 DOM：**[03-html.md](./03-html.md)**  
- 发布：**[04-publish.md](./04-publish.md)**
