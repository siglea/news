# MingoX 内容生产流水线（四步）

编排入口：**`workflow/mingox.py`**（在仓库根目录执行）。

```bash
python3 workflow/mingox.py --help
```

## 目录职责

| 路径 | 职责 |
|------|------|
| **`content/drafts/<slug>/`** | 单篇草稿：第 1 步产出 `01-source.md` 与 `meta.json`；第 2 步产出 `02-annotate-tasks.json`（复合任务 JSON）。 |
| **`workflow/`** | 流水线脚本：`acquire`、`build`、`validate`、`serve`、`deploy`、`wechat`。 |
| **`util/annotate_lib.py`** | 共享词表与 `word-block` 生成（仅 `KEYWORDS` 命中才标注，无兜底凑数）、词汇表、`build_post_html`（微信 CLI 与 MD 草稿共用）。 |
| **`util/.crawl-output/`** | 仅本地抓取缓存（gitignore）；Playwright 可写 `workflow-<slug>-js_content.html`。 |
| **`util/article-profiles.json`** | **微信成稿快捷通道**：一条 profile 对应一篇已抓取的 `js_content` HTML（不经 MD 草稿）。 |
| **`posts/`** | 第 3 步最终静态 HTML。 |
| **`docs/`** | 流水线与前置说明（本文件、`PREREQUISITES.md`）。 |

## 第 1 步：获取原文 → Markdown

输出：`content/drafts/<slug>/01-source.md`，并更新同目录 `meta.json`（若已有则合并字段）。

### 方式 1：直接提供原文（paste）

```bash
python3 workflow/mingox.py init --slug my-topic --title-zh "中文标题" --title-en "English Title" \
  --out-html posts/2026-04-02-my-topic.html
# 写入正文（可编辑器直接改 content/drafts/my-topic/01-source.md）
python3 workflow/mingox.py acquire --slug my-topic --mode paste --file path/to/article.md
# 或管道: cat article.md | python3 workflow/mingox.py acquire --slug my-topic --mode paste
```

### 方式 2：链接抓取（url）

- **微信公众号**：自动调用 `util/crawl-with-playwright.py`，**优先 `--mobile`**（iPhone 微信息 UA，多数情况下 **headless 也可** 拿到正文）；若仍验证页，**去掉 `--headless`**，并加 **`--wait-verify 180`** 在本机窗口内点验证。`acquire` 失败时会 **自动再试桌面 UA**（可用 `--no-mobile-wechat` 跳过移动 UA）。
- **正文进 MD**：先 `extract_ps`（`<p>`）；若段落过少/过短，再 **`extract_wechat_plain_paragraphs` + `extract_wechat_span_leaf_paragraphs` 择优**（解决 section/leaf 排版、避免只剩文末广告 `<p>`）。细节见 [util/README.md](../util/README.md)。
- **`meta.json`**：微信抓取成功时 **`title_zh` 以页面标题为准**（覆盖草稿里旧占位标题）；`source_account` 以 `#js_name` 为准；`footer_template: derivative` 且已有公众号名时，可将 `footer_derivative_mp_unknown` 置为 `false`（`acquire` 在拿到作者时会自动处理）。
- **普通网页**：`trafilatura` 拉取正文（需 `pip install -r workflow/requirements.txt`）。

```bash
python3 workflow/mingox.py acquire --slug my-topic --mode url --url 'https://...'
# 微信：移动 UA + headless（多数环境可行）
python3 workflow/mingox.py acquire --slug my-topic --mode url --url 'https://mp.weixin.qq.com/s/...' --headless
# 微信：验证页 — 有界面 + 等待人工
python3 workflow/mingox.py acquire --slug my-topic --mode url --url 'https://mp.weixin.qq.com/s/...' --wait-verify 180
```

| `acquire` 参数（url） | 含义 |
|----------------------|------|
| `--headless` | Playwright 无头（微信可配合默认移动 UA 使用）。 |
| `--wait-verify SEC` | 出现验证按钮时最多等待 SEC 秒（需非 headless）。 |
| `--no-mobile-wechat` | 不试移动 UA，仅用桌面 Chromium。 |

### 方式 3：摘要/想法 → 检索后再抓取（search）

```bash
python3 workflow/mingox.py acquire --slug my-topic --mode search --query '你的检索句' --list-only
python3 workflow/mingox.py acquire --slug my-topic --mode search --query '...' --pick 0
```

依赖：`duckduckgo-search`。结果质量与合规由人工挑选 `pick` 负责。

---

## 第 2 步：标注 + 机器校验

- **复合任务格式**：`content/drafts/<slug>/02-annotate-tasks.json`  
  - `paragraphs[]`：每项含 `source_text`（来自 MD 段落）与 `html`（已插入 `word-anchor` / `word-block` 的 `<p>...</p>`）。
- **规则对齐**：词形、音标结构等与根目录 [README.md](../README.md)「词汇标注规范」一致；**每 `<p>` 内句密度**等更严规则需人工与范文对照（当前自动化以 **相邻 `word-block` 正则** 为硬门禁）。

```bash
python3 workflow/mingox.py build --slug my-topic
# 跳过相邻检测（仅调试）:
python3 workflow/mingox.py build --slug my-topic --skip-validate
```

全站检查已生成文章：

```bash
python3 workflow/mingox.py validate
```

---

## 第 3 步：生成 HTML

由上一步 **`build`** 完成：读取 `meta.json` 中的 `title_zh` / `title_en` / `out_html` 等，写出 `posts/...html` 并带词汇表。

- **`meta.json`**：`include_source_footer: true` 时插入红色来源块（外源稿）；原创可 `init` 时不加 `--source-footer` 并在 `meta.json` 中保持 `include_source_footer: false`。
- **版权声明版式**：`footer_template` 取 `verbatim`（强调「尽量保留汉字、仅加标注」）或 `derivative`（与 `posts/2026-04-01-private-fund-ai-hiring-threshold.html` 一致的「衍生整理」四段 + 双行风险提示）。`init` 示例：`--footer-template derivative --footer-derivative-mp-unknown`（尚未确认公众号名时首段不写具体帐号）。可选 `source_author_display`、`risk_blurb_secondary`。微信 `acquire` 成功后若已写入 `source_account`，可将 `footer_derivative_mp_unknown` 改为 `false` 并补全作者署名后重建。

---

## 第 4 步：本地或 EdgeOne

```bash
python3 workflow/mingox.py serve --port 8765
python3 workflow/mingox.py deploy --project mingox
```

---

## 微信「profile」捷径（不经 MD 草稿）

已抓取 `util/.crawl-output/...-js_content.html` 时，在 `util/article-profiles.json` 配置后：

```bash
python3 workflow/mingox.py wechat --profile your-profile-key
# 等价: python3 util/annotate-wechat-plain.py --profile your-profile-key
```

---

## 与根 README 的关系

- **版式、列表、词汇、相邻块、外源版权块**：以根目录 [README.md](../README.md) 为权威。
- **本文件**：约定**目录与命令**，避免 `util/` 与草稿职责混淆。
