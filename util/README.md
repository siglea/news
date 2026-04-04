# util：抓取、共享标注库与微信快捷通道

**文档地图**：[docs/README.md](../docs/README.md)。通用编排见 **[docs/PIPELINE.md](../docs/PIPELINE.md)**（含 **主路径 vs Legacy profile** 对照表）、**[docs/steps/](../docs/steps/README.md)** 与 **`workflow/mingox.py`**。本目录侧重：**Playwright 抓取**（第 1 步）、**`annotate_lib` / `annotate_merge` / `md_split`**、以及 **Legacy** **`article-profiles.json` + `annotate-wechat-plain.py`**。

**边界**：`article-profiles.json` **只**给 `annotate-wechat-plain` 用，不是「全局工具配置」；**新稿请用 `content/drafts/` + `mingox`**，勿再新增 profile 条目。

## 依赖（抓取）

```bash
pip3 install -r util/requirements-crawl.txt
python3 -m playwright install
```

## Playwright 抓微信公众号（已验证有效）

桌面 Chrome UA 访问 `mp.weixin.qq.com` 常出现 **「环境异常」验证页**；以下组合在多数环境下 **headless 也可直接拿到 `#js_content`**：

| 做法 | 说明 |
|------|------|
| **`--mobile`** | 使用窄视口 + **iPhone 微信息 User-Agent**（脚本内 `UA_MOBILE_WECHAT`），优先于桌面 UA。 |
| **`page.goto(..., wait_until="domcontentloaded")`** | 微信页用 `load` 易超时；默认 `domcontentloaded`，超时 180s。 |
| **Chromium 参数** | `--disable-blink-features=AutomationControlled`，降低特征暴露。 |
| **验证页人工兜底** | 若仍出现 `#js_verify`：去掉 `--headless`，并加 **`--wait-verify SEC`**，在弹窗里完成验证后再抓。 |

**单独调试抓取（不写草稿）**：

```bash
python3 util/crawl-with-playwright.py --url 'https://mp.weixin.qq.com/s/...' \
  --mobile --out-html util/.crawl-output/debug-js.html --out-meta util/.crawl-output/debug.meta.json
# 需要无人值守时再试：
python3 util/crawl-with-playwright.py --url '...' --mobile --headless --out-html ...
```

**经 `workflow` 调用时**：`acquire` 对微信域名 **先试 `--mobile`，失败再自动试桌面 UA**（见 `workflow/acquire.py`）。`mingox acquire` 额外支持：`--wait-verify`、`--no-mobile-wechat`。

## 微信 `#js_content` → `01-source.md`（段落抽取）

很多推文正文在 **`<section>` + `<span leaf>`** 里，**没有成段的 `<p>`**。若只用 `extract_ps`（只认 `<p>`），`01-source.md` 往往只剩文末运营 `<p>`（广告、话题标签）。

`annotate_lib.py` 中的策略（由 `workflow/acquire.py` 的 `_html_to_source_md` 自动选用）：

| 函数 | 作用 |
|------|------|
| `extract_ps` | 经典微信：正文在 `<p>` 里时足够。 |
| `extract_wechat_plain_paragraphs` | 按 DOM 顺序收集 **全部可见文本**（含姓名高亮等非 `leaf` 节点），按 `。！？；` 切段再打包成段，**避免丢字、断句**（如「赵佳臻」）。 |
| `extract_wechat_span_leaf_paragraphs` | 仅抽 `<span leaf>` 文本作补充；与 plain 比选 **字符总量更大** 的一方。 |

**触发条件**：当 `extract_ps` 结果 **段落数 &lt; 4** 或 **总字符 &lt; 600** 时，启用微信回退路径；否则仍以 `<p>` 为准。

**手工**：首段若残留编辑器符号（如 `▎`），可在 `01-source.md` 里删掉后再 `mingox build`。

## 目录与数据流（推荐编排）

当前设计把 **「爬下来的原始 HTML」** 和 **「成稿页面元数据」** 分开，避免一篇稿子的路径写死在脚本里。

| 路径 | 作用 |
|------|------|
| `util/keyword_lexicon.py` | **`annotate_engine=keywords`** 的全局默认可标注词表（`_KEYWORD_ENTRIES` → `KEYWORD_LEXICON`）。 |
| `util/annotate_lib.py` | **共享逻辑**：从 `keyword_lexicon` 载入 `KEYWORDS`、段落标注（无命中则不插 `word-block`）、`build_post_html`、词汇表行提取；被 `annotate-wechat-plain.py` 与 `workflow/build_draft.py` 共用。 |
| `util/annotate_merge.py` | **MD 草稿**：`chat_json` 的 JSON 校验、去重、逐句 `render_annotated_sentence`；`en` 词位规则与**对义项锚定**见文件内 `CHAT_SYSTEM_PROMPT` 与 **[content/drafts/README.md](../content/drafts/README.md)**。 |
| `util/md_split.py` | `01-source.md` 按空行切段；供 `workflow/build_draft`、`export-chat-bundle`、`synth_llm_annotations_lexicon` 使用。 |
| `util/.crawl-output/` | **仅放爬取结果**（已 `.gitignore`）。可按文章分子目录，避免文件名撞车。 |
| `util/article-profiles.json` | **Legacy**：每篇一条 profile（`crawl_js`、`out_html`、标题、截断规则等）；**勿为新稿扩容**。 |
| `util/annotate-wechat-plain.py` | **Legacy 微信生成器**：读 profile → `#js_content` → `keywords` 式标注 → 写 `posts/*.html`。 |

**Legacy profile 路径为何曾有用**

- 旧流程下新文章可只增 **profile + 抓取文件**，不必改 Python；**当前推荐**改为 **主路径**（`content/drafts/`），见 PIPELINE 对照表。
- 全局词表在 `keyword_lexicon.py` 可多篇共用；若需按主题拆分可后续再拆模块或 `keywords-*.json`（当前未拆）。
- 抓取目录被 ignore，profile 里用相对仓库根的路径指向即可，本地各机器自存 crawl 文件。

**推荐抓取文件命名（示例）**

```text
util/.crawl-output/<article-slug>/js_content.html
# 或沿用微信片段 id：
util/.crawl-output/wechat-<id>-js_content.html
```

在 `article-profiles.json` 里把 `crawl_js` 指到对应文件即可。

## 生成标注正文

默认使用 `article-profiles.json` 里的 `default_profile`：

```bash
python3 util/annotate-wechat-plain.py
```

指定 profile：

```bash
python3 util/annotate-wechat-plain.py --profile dalio-america-decline
```

## 新增一篇文章（流程）

1. 用 Playwright / 现有 `crawl-with-playwright.py`（微信建议 **`--mobile`**）保存 `js_content` 的 HTML 到 `util/.crawl-output/...`。
2. 在 `util/article-profiles.json` 的 `profiles` 中增加一项，必填字段：
   - `crawl_js`：相对仓库根的 HTML 路径。
   - `out_html`：输出的 `posts/....html`。
   - `title_zh` / `title_en` / `source_url`。
   - `meta_description`（可选，空则 `meta` 为空字符串）。
   - 可选版式与页脚：`source_account`（默认 `笔记侠`）、`title_emoji`（默认 `📈`）、`omit_sections_note`、`risk_blurb`（页脚「省略段落说明」与「风险提示」正文）。
3. 截断正文（去文末广告等）：
   - `body_end_marker`：某段 **`<p>` 纯文本** 中出现的子串（如 `不代表笔记侠立场`），命中则截到该段为止。
   - `body_paragraph_cap`：可选；若未命中 marker，最多取前 N 段（安全网，防止拖进全文尾部）。
4. 运行 `python3 util/annotate-wechat-plain.py --profile <你的 key>`。
5. 如需上首页，再改根目录 `index.html` 等（不在本脚本内）。

## 标注规则摘要（与 `annotate-wechat-plain.py` 一致）

- **不改写中文**：只插入 HTML 标注。
- **句切分**：按 `。！？；` 切段；**每小段最多一个** `word-block`（多要点在同一句时只会标一处，这是当前产品限制）。
- **关键词**：`pick_keyword` 在句内取 **命中中文最长** 的 `KEYWORDS` 项；长度相同取 **出现位置最靠左** 的。
- **下划线**：命中关键词时，对应中文包在 `<span class="word-anchor">` 内；`css/style.css` 中为 `.post-content .word-anchor` 下划线。
- **英文词位**：`english-word` 内 **不得含 ASCII 空格**；复合概念用 **连字符一个词位**（如 `gold-surge`、`debt-service`），使英文覆盖与下划线中文 **整段对齐**（避免「黄金暴涨」只标成 `surge` 这类半对应）。
- **无命中**：**不插入** `word-block`（宁缺毋滥）；仅当 `KEYWORDS` 在句内命中中文片段时才标注并生成词汇表行。
- **词汇表**：按正文首次出现的 `english-word` 去重（小写）生成表格。
- **某篇成稿词条过少**：说明正文里的中文术语尚未进入共享 `KEYWORDS`。在**确认该词在稿内确有出现**的前提下，向 `annotate_lib.py` 的 `KEYWORDS` 追加条目（**长词组优先**，`english-word` 仍须无空格、可用连字符），然后对该 slug 重新 `mingox build`；`out_html` 文件名宜与题材一致，勿长期用「permalink / workflow 占位」类名字。

## 相关文件

- `util/crawl-with-playwright.py`：Playwright 抓取相关（`workflow/mingox.py acquire --mode url` 在微信域名下会调用）。
- `util/requirements-crawl.txt`：抓取脚本依赖。
- `workflow/mingox.py`：从 `content/drafts/` 走完整四步时的推荐入口。
