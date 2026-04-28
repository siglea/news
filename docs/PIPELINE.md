# MingoX 内容生产流水线（总览）

第一次阅读建议先看 **[docs/README.md](./README.md)**（文档地图）。

编排入口（仓库根目录）：

```bash
python3 workflow/mingox.py --help
```

## 标准路径

每篇稿件使用 **`content/drafts/<slug>/`**：`meta.json` 与 `01-source.md` 同目录；正文由 **`mingox acquire`** 写入 MD；**`mingox build`** 将 Markdown 段落转为成稿 HTML，并**必须**已有大模型产出的 **`llm_annotations.json`** 以注入词汇标注（缺失则 build 失败）。`build` 默认执行标注质量门禁（占位符、重复 `en`、`meta_description` 非空）。**`slug` 与 `posts/*.html` 文件名均须以文章标题为依据命名**（英文 kebab，推荐 slug 与 `out_html` 主段一致），见 [content/drafts/README.md](../content/drafts/README.md)「命名规范」。其它细则见同文件。

**典型命令**：`mingox init` → `acquire` → `export-chat-bundle` → 大模型写出 `llm_annotations.json` → `build`。
  
**闭环执行（推荐）**：在标注完成后可直接运行 `python3 workflow/mingox.py close-loop --slug <slug>`，固定执行 `build -> validate`；需要发布时再加 `--deploy`。

以往的 **`article-profiles.json` + `annotate-wechat-plain.py` + `mingox wechat`** 已移除；旧流程请改为上述草稿目录 + `build`。

## 四步索引（分步详述）

| 步 | 文档 | 一句话 |
|----|------|--------|
| 1 素材获取 | **[docs/steps/01-acquire.md](./steps/01-acquire.md)** | `init` / `acquire` → `01-source.md` + `meta.json` |
| 2 标注 | **[docs/steps/02-annotate.md](./steps/02-annotate.md)** | 四六级向提示词 + `llm_annotations.json`（**`zh`/`en` 须一一对应**）；**无则 `build` 失败** |
| 3 HTML 成稿 | **[docs/steps/03-html.md](./steps/03-html.md)** | `build` → `posts/*.html`，`validate`，DOM/CSS 契约 |
| 4 发布 | **[docs/steps/04-publish.md](./steps/04-publish.md)** | `serve`、`deploy`、Gitee Pages |

**分步目录索引**：[docs/steps/README.md](./steps/README.md)。**编辑规范**：[EDITORIAL.md](./EDITORIAL.md)。**草稿目录**：[content/drafts/README.md](../content/drafts/README.md)。

**可选代码层解耦（IR / 拆分 build）**：[docs/steps/IR-ROADMAP.md](./steps/IR-ROADMAP.md)（未实现，待评审）。

---

## 目录职责（速查）

| 路径 | 职责 |
|------|------|
| **`content/drafts/<slug>/`** | 单篇草稿：`01-source.md`、`meta.json`；`build` 后生成 `02-annotate-tasks.json`（历史命名，实际为标注结果，`kind=annotate_result`） |
| **`workflow/`** | `mingox.py`：`init`、`acquire`、`build`、`validate`、`serve`、`deploy` 等 |
| **`util/annotate_lib.py`** | 微信/HTML 抽取、`build_post_html`、词汇表反扫 |
| **`util/annotate_merge.py`** | `llm_annotations.json` 合并；bundle 的 `system_prompt` 来自 **`util/prompts/chat_annotate_system.txt`** |
| **`util/.crawl-output/`** | 本地抓取缓存（gitignore） |
| **`posts/`** | 成稿静态 HTML |
| **`docs/`** | 文档地图 [README.md](./README.md)、[PIPELINE.md](./PIPELINE.md)、[EDITORIAL.md](./EDITORIAL.md)、四步分册、[PREREQUISITES.md](./PREREQUISITES.md) |

---

## 环境与其它说明

- **依赖安装**： [PREREQUISITES.md](./PREREQUISITES.md)
- **抓取与 Playwright 细节**： [util/README.md](../util/README.md)
- **版式、版权等编辑规范全文**： [EDITORIAL.md](./EDITORIAL.md)
- **workflow 模块表**： [workflow/README.md](../workflow/README.md)

---

## 与 EDITORIAL / 根 README 的关系

- **列表、标题、外源版权块等编辑规范**：以 [EDITORIAL.md](./EDITORIAL.md) 为权威；根 [README.md](../README.md) 为项目门面与快速链接。
- **本文件与 `docs/steps/`**：约定**步骤边界与命令入口**，避免与 `util/`、草稿职责混淆。

---

## 实战复盘

### 2026-04-13

- **最小闭环**：建议默认按 `init -> acquire(url) -> export-chat-bundle -> llm_annotations.json -> close-loop --deploy` 执行；不要在 `crawl` 成功后提前结束。
- **命名优先**：`slug` 与 `out_html` 先对齐标题语义再开工，可减少后续改名与首页链接同步成本。
- **门禁理解**：`validate` 的 `density heuristic WARN` 是提示项；`OK adjacent check` 才是阻断门禁是否通过的核心信号。

### 2026-04-16（吴晓波/beauvoir 修复后追加）

- **首页同步是发布的一部分**：`build + validate + deploy` 通过≠发布完成。**必须**同步更新 `index.html` 的 `<ul class="post-list">`，否则读者在首页看不到新稿。`close-loop` 命令不替代这一步。
- **临时 slug 必须清理**：若先用 `wechat-<id>` 探路抓取，确认正式 slug 后须**立即删除**临时目录，不要让它进入提交。
- **`out_html` 日期必须与 `meta.date` 一致**：`init` 时的 `--out-html` 日期须为**当天**，与 `meta.json` 中自动填入的 `date` 对齐；事后发现不一致须在 build 前修正。
- **正文尾部非正文必须清除**：`acquire` 后须检查 `01-source.md` 末尾是否残留编辑署名、图源、运营文案等非正文段落，清除后再进入标注。
- **`title_emoji` 须按题材选择**：`📈` 用于新闻/财经；`💡` 用于思想/观点/人文；`📜` 用于文化/诗词。不要一律用默认值。
- **对话场景下禁止偷懒用词表兜底**：在任何可对话场景中，**必须**按 `system_prompt` 逐句生成标注（目标 ≥80% 非 skip），而非直接跑 `bundle_lexicon_annotate.py`。词表兜底仅适用于无对话环境。
- **外源稿须开启版权声明**：微信公众号转载稿的 `include_source_footer` 应为 `true`，`footer_template` 应选 `derivative`，并填写 `source_author_display`。

---

## 验证链接须走到发布

当任务是**检验/验证**某篇文章 URL（尤其是微信公众号）时，确认抓取可行后**默认继续完成整条主路径并执行发布**，不要停在「单独 crawl 成功」就结束。

**推荐顺序**：

1. `mingox init` → `mingox acquire --mode url`（或先用 `util/crawl-with-playwright.py` 探路后再 acquire）。
2. 补全 `meta.json`（`meta_description`、`risk_blurb_secondary`、`omit_sections_note` 等，按 [EDITORIAL.md](./EDITORIAL.md)）。
3. `export-chat-bundle` → 按 [02-annotate.md](./steps/02-annotate.md) 产出 `llm_annotations.json`（**build 必填**） → `mingox build`。
4. 更新根目录 `index.html` 列表（新稿置顶）。
5. `mingox validate --post posts/...html`。
6. `mingox deploy --project mingox`；若无密钥则说明阻塞原因。

**部署结果汇报**：每次都必须写出完整预览地址（须含 `?eo_token=...` 全部查询参数），勿只写「部署成功」而不给链接。

`util/.crawl-output/` 仅作缓存，**不替代** `content/drafts/<slug>/` 与 `posts/*.html` 成稿。

---

## 新稿全流程闭环检查

从 URL/paste 生产一篇新稿并发布时，**必须**按以下顺序逐项完成。任何一步遗漏都可能导致"部署了但读者看不到"或"内容质量不达标"。

### 1. init — 命名与元数据

- `--slug` 以文章标题凝练英文 kebab（禁止 `wechat-<id>` 等随机串）。
- `--out-html` 日期为**当天**，与 `meta.json` 自动填入的 `date` 一致。
- `--title-emoji` 按题材选：`📈` 财经、`💡` 思想/观点、`📜` 文化/诗词。
- 外源稿须加 `--source-footer --footer-template derivative --source-author-display "xxx"`。

### 2. acquire — 抓取后自检

- 打开 `01-source.md`，删除末尾编辑署名、图源、公众号关注等非正文行。
- 确认 `meta.json` 的 `title_zh`、`title_en`、`meta_description` 均已填写且准确。
- 若先用临时 slug 探路，确认正式 slug 后**立即删除**临时目录。

### 3. annotate — 标注质量

- **对话场景下必须按 `system_prompt` 逐句生成标注**，目标 ≥80% 非 skip。
- **禁止**在有对话能力时偷懒跑 `bundle_lexicon_annotate.py` 词表兜底。
- 保存前自检：每条 `zh` 在对应句正文中逐字出现？`en` 一一对应？无并列短语？

### 4. build + validate

- `mingox build` 通过质量门禁（无 FAIL）。
- `mingox validate` 的 `adjacent check` 为 OK。

### 5. index.html — 首页入口

- **在 `index.html` 的 `<ul class="post-list">` 顶部添加新稿的 `<li>`**。
- 标题、日期、标签、摘要格式符合 EDITORIAL.md。
- `deploy` 成功 ≠ 发布完成；首页看不到等于白发。

### 6. deploy + commit + push

- 部署后回传**完整预览链接**（含 `?eo_token=...`）。
- git commit + push。
