# 草稿目录 `content/drafts/<slug>/`

每篇待发布内容一个子目录（`slug` 用小写、连字符）。

## 文件一览

| 文件 | 说明 |
|------|------|
| `meta.json` | 标题、英文题、`out_html`、来源 URL、`include_source_footer`、`footer_template`（`verbatim` \| `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary` 等。可用 `python3 workflow/mingox.py init ...` 生成模板。 |
| `out_html` 命名 | **`posts/YYYY-MM-DD-<题材>.html`**：`<题材>` 为**可读英文 kebab**（人名、公司、主题词），与范文 `posts/2026-04-03-pinduoduo-xinpinmu-supply-chain.html` 一致。**禁止**用草稿目录名或微信文章 id 当文件名（如 `wechat-ymssqxei`）；`init` 的 `--slug` 可与 `out_html` 不同。改路径后需同步 `index.html` 与站内链接。 |
| `01-source.md` | **第 1 步**输出的正文（Markdown，按空行分段）。微信 HTML 以 section/leaf 为主时，由 `annotate_lib` 的 **plain/leaf 回退抽取**生成；偶见首段符号（如 `▎`）可手删后重建。 |
| `02-annotate-tasks.json` | **`mingox build` 生成的**段落快照（`source_text` + 当前实现下的 `html`，便于 diff）。 |
| **`llm_annotations.json`** | **必填**：按 [docs/steps/02-annotate.md](../../docs/steps/02-annotate.md) 产出（大模型或 `bundle_lexicon_annotate` 词表）；**`zh` 须与 `en` 义项一一对应**，禁止长串中文只配部分义项的英文。可用 `meta.llm_annotations_file` 改文件名。 |
| `llm-chat-bundle.json` | （可选）`export-chat-bundle` 导出，内含 `system_prompt` 与逐句 `sentences`。 |

抓取缓存仍在 **`util/.crawl-output/`**（不提交），此处只放编辑定稿与元数据。微信抓取技巧与段落抽取逻辑见 **[util/README.md](../../util/README.md)**。

---

## 成稿流程（当前）

1. **`python3 workflow/mingox.py init ...`**（或已有 `meta.json`）  
2. **`python3 workflow/mingox.py acquire ...`** → `01-source.md`  
3. **`export-chat-bundle`** → 大模型产出 **`llm_annotations.json`**（四六级向提示词见 [02-annotate.md](../../docs/steps/02-annotate.md)）  
4. **`python3 workflow/mingox.py build --slug <slug>`** → `02-annotate-tasks.json` + `posts/*.html`（无 `llm_annotations.json` 时 **build 失败**）

**流水线总览**：[PIPELINE.md](../../docs/PIPELINE.md)。**标注步骤**：[docs/steps/02-annotate.md](../../docs/steps/02-annotate.md)。**HTML 成稿**：[docs/steps/03-html.md](../../docs/steps/03-html.md)。四步索引见 **[docs/steps/README.md](../../docs/steps/README.md)**。

**`meta.json`（微信 `url` 抓取后）**：**`title_zh` 会被更新为微信页标题**（覆盖 init 时的占位题）；`source_account` 等为抓取侧写入。英文题、`meta_description`、风险提示等常需 **人工补全** 后再 `build`。
