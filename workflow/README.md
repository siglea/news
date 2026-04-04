# workflow：四步流水线脚本

- **总览**：[docs/PIPELINE.md](../docs/PIPELINE.md)  
- **分步文档**：[docs/steps/README.md](../docs/steps/README.md)（01 取材 / 02 标注 / 03 HTML / 04 发布）  
- **前置**：[docs/PREREQUISITES.md](../docs/PREREQUISITES.md)

## 一键入口

```bash
python3 workflow/mingox.py --help
```

## 模块

| 文件 | 作用 |
|------|------|
| `mingox.py` | CLI：`init` / `acquire` / `build` / `validate` / `serve` / `deploy` / `wechat` |
| `acquire.py` | 第 1 步：paste / url / search → `01-source.md`；微信 url **先试 Playwright `--mobile`**，失败再桌面 UA；MD 用 `extract_ps` + 微信 plain/leaf 回退（见 util/README）。 |
| `build_draft.py` | 第 2–3 步（实现上同一 `build`）：`01-source.md` → `02-annotate-tasks.json` + `posts/*.html`；`meta.annotate_engine` 支持 **`chat_json`**（默认推荐）/ **`keywords`**；分步说明见 [docs/steps/02-annotate.md](../docs/steps/02-annotate.md)、[docs/steps/03-html.md](../docs/steps/03-html.md)。 |
| `validate.py` | 相邻 `word-block` 检测（与根 README 一致） |
| `md_split.py` | Markdown 按空行切段 |
| `paths.py` | 仓库根路径 |
| `requirements.txt` | URL 提取与搜索可选依赖 |

## 与 `util/` 的分工

- **`util/keyword_lexicon.py`**：全局 `keywords` 词表；**`util/annotate_lib.py`**：标注与页面壳（被 `annotate-wechat-plain.py` 与本目录 `build_draft.py` 共用）。
- **`util/crawl-with-playwright.py`**：微信等强反爬页，由 `acquire.py` 在 url 模式下调用。
- **`util/article-profiles.json`**：仅服务 **微信 profile** 快捷路径，不替代 `content/drafts/` 通用流水线。
