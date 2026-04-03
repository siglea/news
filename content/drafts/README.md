# 草稿目录 `content/drafts/<slug>/`

每篇待发布内容一个子目录（`slug` 用小写、连字符）。

## 文件一览

| 文件 | 说明 |
|------|------|
| `meta.json` | 标题、英文题、`out_html`、来源 URL、`include_source_footer`、`footer_template`（`verbatim` \| `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary`、**`annotate_engine`**（见下）等。可用 `python3 workflow/mingox.py init ...` 生成模板。 |
| `out_html` 命名 | 建议与**题材一致**（如 `posts/2026-04-03-pinduoduo-xinpinmu-supply-chain.html`），避免沿用流水线占位名；改路径后需同步 `index.html` 与站内链接。 |
| `01-source.md` | **第 1 步**输出的正文（Markdown，按空行分段）。微信 HTML 以 section/leaf 为主时，由 `annotate_lib` 的 **plain/leaf 回退抽取**生成；偶见首段符号（如 `▎`）可手删后重建。 |
| `02-annotate-tasks.json` | **第 2 步**由 `mingox build` 生成的复合任务快照（可复查、可版本管理）。 |
| **`terms.json`** | （可选）当 `meta.annotate_engine` 为 **`terms_json`** 时，**人工维护的词表**，build 的**唯一真源**；格式见下文「`terms.json` 词表规则」。 |
| **`llm_annotations.json`** | （可选）对话或 `_gen_ann.py` 生成的逐句标注快照；**在 `terms_json` 模式下不参与 build**，仅便于 diff/核对。 |
| `llm-chat-bundle.json` | （可选）`export-chat-bundle` 导出，供 `chat_json` 对话使用。 |

抓取缓存仍在 **`util/.crawl-output/`**（不提交），此处只放编辑定稿与元数据。微信抓取技巧与段落抽取逻辑见 **[util/README.md](../../util/README.md)**。

---

## 标注引擎（`meta.json`）

| `annotate_engine` | 行为 |
|-------------------|------|
| 省略或 **`keywords`** | 使用 `util/annotate_lib.py` 的 **`KEYWORDS`** 子串匹配；`keyword_dedupe: false` 可关闭全文按英文词形去重。 |
| **`terms_json`** | **直接读 `terms.json`**（路径由 `terms_file` 指定，默认 `terms.json`），按句最长 `match` 贪心匹配，**全文 `en` 小写去重**；**不依赖** `llm_annotations.json`。适合「从正文人工选词 + 写英文/音标」的稳定流程。 |
| **`chat_json`** | 读 **`llm_annotations_file`**（默认 `llm_annotations.json`），经 `util/annotate_merge.py` 校验、去重后渲染。先 `python3 workflow/mingox.py export-chat-bundle --slug <slug>` 再对话产出 JSON。 |

命令与总览见 **[docs/PIPELINE.md](../../docs/PIPELINE.md)**。

---

## 推荐工作流（从 `01-source.md` 出发）

1. **在正文里选词**：片段须是 `01-source.md` 去掉标点后、句内**逐字可找到的连续子串**（宁缺毋滥）。  
2. **写入 `terms.json`**：为每条补 `en` / `ipa` / `pos` / `gloss`，并保证 **中英「同位锚定」**（见下）。  
3. **`meta.json`** 设 `"annotate_engine": "terms_json"`、`"terms_file": "terms.json"`。  
4. **`python3 workflow/mingox.py build --slug <slug>`** → 生成 `02-annotate-tasks.json` 与 `posts/*.html`。  

可选：在同目录执行 **`python3 content/drafts/<slug>/_gen_ann.py`**（若存在），从 `terms.json` 重写 **`llm_annotations.json`**，仅用于版本对比，**不改变** `terms_json` build 结果。

---

## `terms.json` 词表规则

文件为 JSON **数组**，每项为对象，字段如下。

| 字段 | 必填 | 说明 |
|------|------|------|
| **`zh`** | 是 | 正文里实际**下划线对应**的最短连续子串；与 `en` / `ipa` / `pos` / `gloss` **指同一义项**。 |
| **`en`** | 是 | **单个英文词位**：无 ASCII 空格；允许 `nonGAAP` 这类**句点**；允许 **`soft-skill` 式连字符**，且每一段均为字母数字（与 `util/annotate_merge.py` 中 `en_headword_token_ok` 一致）。 |
| **`ipa`** | 是 | 方括号国际音标，如 `[ˈɜːnɪŋz]`。 |
| **`pos`** | 是 | 如 `n.`、`v.`、`adj.`。 |
| **`gloss`** | 是 | **只解释本条 `en`** 的中文释义；不得写成整句摘要或与 `en` 无关的旁白。为空则在 `chat_json` 合并时会被丢弃。 |
| **`match`** | 否 | 当仅靠短 `zh` 无法在句中唯一定位时，填正文里**更长的连续子串**，且必须 **包含整个 `zh`**（`zh` 为 `match` 子串）。匹配时要求 **`match` 与 `zh` 同时出现在该句 body 中**。 |

程序按 **`len(match)` 降序**尝试匹配（无 `match` 时以 `zh` 为 `match`），每条英文词形全文仅用一次。

---

## 中英对齐范式（对义项锚定）

**原则**：`en` 必须是读者看到这段 **`zh`** 时，**最直接对应的英文词/复合词**（同位释义），用于词汇表「中文—英文」对齐。

**避免**：

- 用**同句或同话题里相关但不同位**的词顶替，例如：「学习轨迹」对 **trajectory / path**，不要对 **analytics**；「数字员工」对岗位/分身类概念，不要对 **staffing**（编制配置）；「财务业绩」在财报语境对 **earnings** 等，不要仅用泛称 **results**；「品牌出海」对 **outbound** 等外向扩张义，不要仅用泛称 **globalization**；「龙头壁垒」若正文无「护城河」比喻，优先 **barrier** 等与「壁垒」字面/商业义对齐的词，避免强行 **moat**。
- **`gloss` 写成中文片段的复述**却不解释 **`en`**（如用「联合领投」解释 *syndicate* 而不用「银团」类义项）。

**`chat_json` / 对话产出**：须遵守 `export-chat-bundle` 内 **`system_prompt`**（含上述义项锚定与 `zh` 最短化等条）。若同时使用 **`underline`**，合并时会**折叠为最短 `zh`**（以 `underline` 为准）；新稿建议只写最短 **`zh`**，不填 `underline`。

---

## 词汇偏少（`keywords` 模式）

自动化仅标注 `util/annotate_lib.py` 的 **`KEYWORDS`** 与正文**字面命中**的片段（宁缺毋滥）。若成稿「重点词汇」表过短，在 **KEYWORDS 中增补该稿实际出现的术语**（长短语优先、英文词位无空格、可用连字符），再 `mingox build`。

**`meta.json`（微信 `url` 抓取后）**：**`title_zh` 会被更新为微信页标题**（覆盖 init 时的占位题）；`source_account` 等为抓取侧写入。英文题、`meta_description`、风险提示等常需 **人工补全** 后再 `build`。
