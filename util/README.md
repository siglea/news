# util：抓取与成稿共享库

**文档地图**：[docs/README.md](../docs/README.md)。通用编排见 **[docs/PIPELINE.md](../docs/PIPELINE.md)**、**[docs/steps/](../docs/steps/README.md)** 与 **`workflow/mingox.py`**。本目录侧重：**Playwright 抓取**（第 1 步）、**`annotate_lib` / `md_split`**。

**边界**：成稿元数据与正文真源一律在 **`content/drafts/<slug>/`**（`meta.json`、`01-source.md`）；不再提供 `article-profiles` 捷径。

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

| 路径 | 作用 |
|------|------|
| `util/annotate_lib.py` | 微信/HTML 抽取、`split_sentences`、`render_annotated_sentence`、`build_post_html`、词汇表反扫 |
| `util/annotate_merge.py` | `llm_annotations.json` 合并；`export_chat_bundle_dict`；`CHAT_SYSTEM_PROMPT` 由 **`util/prompts/chat_annotate_system.txt`** 加载 |
| `util/md_split.py` | `01-source.md` 按空行切段；供 `build_draft` / `export-chat-bundle` |
| `util/.crawl-output/` | **仅放爬取结果**（已 `.gitignore`）。可按文章分子目录，避免文件名撞车 |

**推荐抓取缓存命名（示例，仅供 `acquire` 调试时参考）**

```text
util/.crawl-output/<article-slug>/js_content.html
# 或沿用微信片段 id：
util/.crawl-output/wechat-<id>-js_content.html
```

正式流水线以 **`mingox acquire --mode url`** 写入 `content/drafts/<slug>/01-source.md`，无需手填 profile。

## 相关文件

- `util/crawl-with-playwright.py`：Playwright 抓取相关（`workflow/mingox.py acquire --mode url` 在微信域名下会调用）。
- `util/requirements-crawl.txt`：抓取脚本依赖。
- `workflow/mingox.py`：从 `content/drafts/` 走流水线时的推荐入口。
