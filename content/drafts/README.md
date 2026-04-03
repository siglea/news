# 草稿目录 `content/drafts/<slug>/`

每篇待发布内容一个子目录（`slug` 用小写、连字符）。

| 文件 | 说明 |
|------|------|
| `meta.json` | 标题、英文题、`out_html`、来源 URL、`include_source_footer`、`footer_template`（`verbatim` \| `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary` 等。可用 `python3 workflow/mingox.py init ...` 生成模板。 |
| `out_html` 命名 | 建议与**题材一致**（如 `posts/2026-04-03-pinduoduo-xinpinmu-supply-chain.html`），避免沿用流水线占位名；改路径后需同步 `index.html` 与站内链接。 |
| 词汇偏少时 | 自动化仅标注 `util/annotate_lib.py` 的 `KEYWORDS` 与正文**字面命中**的片段（宁缺毋滥、无兜底硬凑）。若成稿「重点词汇」表过短，应在 **KEYWORDS 中增补该稿实际出现的术语**（长短语优先、英文词位用连字符一个词），再 `mingox build`。 |
| `meta.json`（微信 `url` 抓取后） | **`title_zh` 会被更新为微信页标题**（覆盖 init 时的占位题）；`source_account` 等为抓取侧写入。英文题、`meta_description`、风险提示等常需 **人工补全** 后再 `build`。 |
| `01-source.md` | **第 1 步**输出的正文（Markdown，按空行分段）。微信 HTML 以 section/leaf 为主时，由 `annotate_lib` 的 **plain/leaf 回退抽取**生成；偶见首段符号（如 `▎`）可手删后重建。 |
| `02-annotate-tasks.json` | **第 2 步**由 `mingox build` 生成的复合任务快照（可复查、可版本管理）。 |

抓取缓存仍在 **`util/.crawl-output/`**（不提交），此处只放编辑定稿与元数据。微信抓取技巧与段落抽取逻辑见 **[util/README.md](../../util/README.md)**。
