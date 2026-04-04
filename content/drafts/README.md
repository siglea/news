# 草稿目录 `content/drafts/<slug>/`

每篇待发布内容一个子目录（`slug` 用小写、连字符）。

## 文件一览

| 文件 | 说明 |
|------|------|
| `meta.json` | 标题、英文题、`out_html`、来源 URL、`include_source_footer`、`footer_template`（`verbatim` \| `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary`、**`annotate_engine`**（见下）等。可用 `python3 workflow/mingox.py init ...` 生成模板。 |
| `out_html` 命名 | **`posts/YYYY-MM-DD-<题材>.html`**：`<题材>` 为**可读英文 kebab**（人名、公司、主题词），与范文 `posts/2026-04-03-pinduoduo-xinpinmu-supply-chain.html` 一致。**禁止**用草稿目录名或微信文章 id 当文件名（如 `wechat-ymssqxei`）；`init` 的 `--slug` 可与 `out_html` 不同。改路径后需同步 `index.html` 与站内链接。 |
| `01-source.md` | **第 1 步**输出的正文（Markdown，按空行分段）。微信 HTML 以 section/leaf 为主时，由 `annotate_lib` 的 **plain/leaf 回退抽取**生成；偶见首段符号（如 `▎`）可手删后重建。 |
| `02-annotate-tasks.json` | **第 2 步**由 `mingox build` 生成的复合任务快照（可复查、可版本管理）。 |
| **`llm_annotations.json`** | 当 `annotate_engine` 为 **`chat_json`** 时，由对话按 bundle 的 `system_prompt` 产出的逐句标注 JSON，**build 真源**。也可用 `python3 workflow/synth_llm_annotations_lexicon.py <slug>` 从正文 + 全局词表生成**初稿**（见下）。 |
| `annotate_lexicon_extra.json` | （可选）与本篇正文配套的补充词条，`{"entries":[{zh,en,ipa,pos,gloss},...]}`；`synth_llm_annotations_lexicon.py` 会并入后再按句匹配。 |
| `llm-chat-bundle.json` | （可选）`export-chat-bundle` 导出，供 `chat_json` 对话使用。 |

抓取缓存仍在 **`util/.crawl-output/`**（不提交），此处只放编辑定稿与元数据。微信抓取技巧与段落抽取逻辑见 **[util/README.md](../../util/README.md)**。

---

## 标注引擎（`meta.json`）

**仓库约定**：**默认 `chat_json`**；**只有编者单独说明「本篇用 keywords」等时**才改 `annotate_engine`。不要用 `keywords` 替代对话标注，除非明确要求（否则词汇密度往往远低于 [EDITORIAL.md](../../docs/EDITORIAL.md)）。

| `annotate_engine` | 行为 |
|-------------------|------|
| **`chat_json`**（**默认推荐新稿**） | 读 **`llm_annotations_file`**（默认 `llm_annotations.json`），经 `util/annotate_merge.py` 校验、去重后渲染。先 `python3 workflow/mingox.py export-chat-bundle --slug <slug>` 再对话产出 JSON。 |
| **`keywords`**（非默认；**须 `meta` 显式写出**，且仅编者单独要求时使用） | 使用仓库全局词表 [util/keyword_lexicon.py](../../util/keyword_lexicon.py)（经 `annotate_lib` 暴露为 **`KEYWORDS`**）做子串匹配；`keyword_dedupe: false` 可关闭全文按英文词形去重。 |

**标注环节总览**（引擎决策树、真源禁区、`validate` 能力边界）：**[docs/ANNOTATION.md](../../docs/ANNOTATION.md)**。**第 2 步分册**：[docs/steps/02-annotate.md](../../docs/steps/02-annotate.md)。四步索引见 **[docs/steps/README.md](../../docs/steps/README.md)**、[PIPELINE.md](../../docs/PIPELINE.md)。

---

## 推荐工作流（从 `01-source.md` 出发，**`chat_json` 主路径**）

1. **`python3 workflow/mingox.py export-chat-bundle --slug <slug>`**，将 bundle 中的 `system_prompt` 与 `sentences` 交给助手，产出 **`{"version":1,"annotations":[...]}`**，保存为 **`llm_annotations.json`**。若需**无对话初稿**，可先在同目录放 `annotate_lexicon_extra.json`（可选），再运行 **`python3 workflow/synth_llm_annotations_lexicon.py <slug>`**。  
2. **`meta.json`** 设 **`"annotate_engine": "chat_json"`**（及可选的 `llm_annotations_file`）。  
3. **`python3 workflow/mingox.py build --slug <slug>`** → 生成 `02-annotate-tasks.json` 与 `posts/*.html`。  
4. 若合并 stderr 提示缺句/校验失败，**改 JSON 或再开一轮对话**补全；成稿后仍按 [docs/EDITORIAL.md](../../docs/EDITORIAL.md) 做密度与相邻块人工扫。  

---

## 中英对齐范式（对义项锚定）

**原则**：`en` 必须是读者看到这段 **`zh`** 时，**最直接对应的英文词/复合词**（同位释义），用于词汇表「中文—英文」对齐。

**避免**：

- 用**同句或同话题里相关但不同位**的词顶替，例如：「学习轨迹」对 **trajectory / path**，不要对 **analytics**；「数字员工」对岗位/分身类概念，不要对 **staffing**（编制配置）；「财务业绩」在财报语境对 **earnings** 等，不要仅用泛称 **results**；「品牌出海」对 **outbound** 等外向扩张义，不要仅用泛称 **globalization**；「龙头壁垒」若正文无「护城河」比喻，优先 **barrier** 等与「壁垒」字面/商业义对齐的词，避免强行 **moat**。
- **`gloss` 写成中文片段的复述**却不解释 **`en`**（如用「联合领投」解释 *syndicate* 而不用「银团」类义项）。

**`chat_json` / 对话产出**：须遵守 `export-chat-bundle` 内 **`system_prompt`**（含上述义项锚定与 `zh` 最短化等条）。若同时使用 **`underline`**，合并时会**折叠为最短 `zh`**（以 `underline` 为准）；新稿建议只写最短 **`zh`**，不填 `underline`。

---

## 词汇偏少（`keywords` 模式）

自动化仅标注全局词表 [util/keyword_lexicon.py](../../util/keyword_lexicon.py) 与正文**字面命中**的片段（宁缺毋滥）。若成稿「重点词汇」表过短，在 **`_KEYWORD_ENTRIES` 中增补该稿实际出现的术语**（长短语优先、英文词位无空格、可用连字符），再 `mingox build`。

**`meta.json`（微信 `url` 抓取后）**：**`title_zh` 会被更新为微信页标题**（覆盖 init 时的占位题）；`source_account` 等为抓取侧写入。英文题、`meta_description`、风险提示等常需 **人工补全** 后再 `build`。
