# 第 1 步：素材获取 → Markdown

**产出**：`content/drafts/<slug>/01-source.md`，并合并更新同目录 **`meta.json`**。

**命令**：`python3 workflow/mingox.py init ...`、`python3 workflow/mingox.py acquire ...`（详见下文）。

**下一步**：[02-annotate.md](./02-annotate.md)（标注流程待重新定义）→ `mingox build`。

**命名**：`--slug`（草稿目录）与 `init` 的 **`--out-html`（posts 下文件名）** 均须**以文章标题为依据**凝练英文 kebab；**推荐**二者主段一致。全文见 **[content/drafts/README.md](../../content/drafts/README.md)**「命名规范」。

---

## 方式 1：直接提供原文（paste）

```bash
python3 workflow/mingox.py init --slug my-topic --title-zh "中文标题" --title-en "English Title" \
  --out-html posts/2026-04-02-topic-in-english-kebab.html
python3 workflow/mingox.py acquire --slug my-topic --mode paste --file path/to/article.md
# 或管道: cat article.md | python3 workflow/mingox.py acquire --slug my-topic --mode paste
```

---

## 方式 2：链接抓取（url）

- **微信公众号**：`acquire` 调用 `util/crawl-with-playwright.py`，**优先移动 UA（`--mobile`）**；验证页需有界面 + `--wait-verify`。失败时会再试桌面 UA（可用 `--no-mobile-wechat` 跳过移动 UA）。
- **正文进 MD**：`extract_ps`（`<p>`）；段落过少时再 **plain/leaf 回退**。细节见 **[util/README.md](../../util/README.md)**。
- **`meta.json`**：微信抓取成功时 **`title_zh` 以页面标题为准**；`source_account` 以 `#js_name` 为准；`footer_derivative_mp_unknown` 等见 `meta` 模板说明。

```bash
python3 workflow/mingox.py acquire --slug my-topic --mode url --url 'https://...'
python3 workflow/mingox.py acquire --slug my-topic --mode url --url 'https://mp.weixin.qq.com/s/...' --headless
python3 workflow/mingox.py acquire --slug my-topic --mode url --url 'https://mp.weixin.qq.com/s/...' --wait-verify 180
```

| `acquire` 参数（url） | 含义 |
|----------------------|------|
| `--headless` | Playwright 无头。 |
| `--wait-verify SEC` | 验证页最多等待 SEC 秒（需非 headless）。 |
| `--no-mobile-wechat` | 不试移动 UA。 |

### 微信抓取实战要点

- 建议先用 `mingox acquire --mode url` 直跑；遇到「环境异常」或验证页，再切非 headless 并加 `--wait-verify 180` 由本机人工完成验证。
- 若需要先探路，可单独运行 `util/crawl-with-playwright.py` 确认 `title/author/content_len` 再回到流水线命令。
- 微信场景下 `headless` 并非一定失败；可先试，再按验证页情况降级到可视化抓取。

---

## 方式 3：检索后再抓取（search）

```bash
python3 workflow/mingox.py acquire --slug my-topic --mode search --query '你的检索句' --list-only
python3 workflow/mingox.py acquire --slug my-topic --mode search --query '...' --pick 0
```

依赖：`duckduckgo-search`（见 [workflow/requirements.txt](../../workflow/requirements.txt)）。

---

## 相关路径

| 路径 | 说明 |
|------|------|
| `content/drafts/<slug>/` | 草稿根目录 |
| `util/.crawl-output/` | 本地抓取缓存（gitignore） |
| `util/crawl-with-playwright.py` | 微信等强反爬 |
| `workflow/acquire.py` | 第 1 步实现 |

**反爬与 Playwright 细节**：[util/README.md](../../util/README.md)。**环境安装**：[PREREQUISITES.md](../PREREQUISITES.md)。

---

## acquire 后自检清单（进入标注前必过）

1. **正文尾部清理**：打开 `01-source.md`，检查末尾是否残留「本篇作者 | …」「主编 | …」「图源 | …」「责任编辑」「关注公众号」等非正文行，有则删除。
2. **`meta.json` 核对**：
   - `title_zh`：是否与原文标题一致（微信抓取会自动填入页面标题，需确认）。
   - `title_en`：是否已补充有意义的英文标题（`acquire` 不自动填写英文题）。
   - `title_emoji`：是否按题材选择了正确 emoji（`📈` 财经、`💡` 思想/观点、`📜` 文化/诗词、`🎙️` 播客）。
   - `out_html` 日期部分：是否与 `date` 字段一致且为当天。
   - `meta_description`：是否已填写一句话摘要（不可为空，门禁会拦截）。
   - `include_source_footer` / `footer_template`：外源稿须开启（`true` + `derivative`），并填写 `source_author_display`。
3. **临时 slug 清理**：若先用临时名称（如 `wechat-<id>`）探路抓取，确认正式 slug 后须删除临时目录。
