# 第 1 步：素材获取 → Markdown

**产出**：`content/drafts/<slug>/01-source.md`，并合并更新同目录 **`meta.json`**。

**命令**：`python3 workflow/mingox.py init ...`、`python3 workflow/mingox.py acquire ...`（详见下文）。

**下一步**：[02-annotate.md](./02-annotate.md)（在正文稳定后再选标注引擎）。

**`mingox init`** 写出的 `meta.json` **默认包含** `"annotate_engine": "chat_json"`。若某草稿从未经 `init`、且 `meta.json` 里没有该字段，`build` 仍按程序默认走 **`keywords`**（见 [workflow/build_draft.py](../../workflow/build_draft.py)）。

---

## 方式 1：直接提供原文（paste）

```bash
python3 workflow/mingox.py init --slug my-topic --title-zh "中文标题" --title-en "English Title" \
  --out-html posts/2026-04-02-my-topic.html
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
