# workflow：四步流水线脚本

- **文档地图**：[docs/README.md](../docs/README.md)  
- **总览**：[docs/PIPELINE.md](../docs/PIPELINE.md)  
- **分步文档**：[docs/steps/README.md](../docs/steps/README.md)（01 取材 / 02 标注占位 / 03 HTML / 04 发布）  
- **前置**：[docs/PREREQUISITES.md](../docs/PREREQUISITES.md)  
- **编辑规范**：[docs/EDITORIAL.md](../docs/EDITORIAL.md)

## 一键入口

```bash
python3 workflow/mingox.py --help
```

## 模块

| 文件 | 作用 |
|------|------|
| `mingox.py` | CLI：`init` / `acquire` / `build` / `export-chat-bundle` / `validate` / `serve` / `deploy` |
| `acquire.py` | 第 1 步：paste / url / search → `01-source.md`；微信 url **先试 Playwright `--mobile`**，失败再桌面 UA；MD 用 `extract_ps` + 微信 plain/leaf 回退（见 util/README）。 |
| `build_draft.py` | `01-source.md` → `02-annotate-tasks.json` + `posts/*.html`；若存在 `llm_annotations.json` 则合并标注（[02-annotate.md](../docs/steps/02-annotate.md)）。 |
| `validate.py` | 相邻 `word-block` 检测（针对含标注的 HTML）；密度启发式 WARN |
| `paths.py` | 仓库根路径 |
| `build_deploy_site.py` | EdgeOne 专用：生成 **`site/`** 最小静态树（见根目录 **`edgeone.json`**），避免部署包文件数超限 |
| `requirements.txt` | URL 提取与搜索可选依赖 |

## 与 `util/` 的分工

- **`util/annotate_lib.py`**：微信抽取、`build_post_html`、词汇表反扫（正文含 `word-block` 时）。
- **`util/crawl-with-playwright.py`**：微信等强反爬页，由 `acquire.py` 在 url 模式下调用。
- **`util/md_split.py`**：Markdown 按空行切段；`build_draft` 使用。
