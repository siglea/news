# workflow：四步流水线脚本

- **文档地图**：[docs/README.md](../docs/README.md)  
- **总览**：[docs/PIPELINE.md](../docs/PIPELINE.md)  
- **分步文档**：[docs/steps/README.md](../docs/steps/README.md)（01 取材 / 02 标注 / 03 HTML / 04 发布）  
- **前置**：[docs/PREREQUISITES.md](../docs/PREREQUISITES.md)  
- **编辑规范**：[docs/EDITORIAL.md](../docs/EDITORIAL.md)

## 一键入口

```bash
python3 workflow/mingox.py --help
```

## 模块

| 文件 | 作用 |
|------|------|
| `mingox.py` | CLI：`init` / `acquire` / `build` / `export-chat-bundle` / `synth-lexicon-annotations` / `validate` / `serve` / `deploy` |
| `acquire.py` | 第 1 步：paste / url / search → `01-source.md`；微信 url **先试 Playwright `--mobile`**，失败再桌面 UA；MD 用 `extract_ps` + 微信 plain/leaf 回退（见 util/README）。 |
| `build_draft.py` | 第 2–3 步（实现上同一 `build`）：`01-source.md` → `02-annotate-tasks.json` + `posts/*.html`；`meta.annotate_engine` 省略时**按仓库约定默认为 `chat_json`**；`keywords` 须显式写出（仅编者单独要求某篇时使用）；分步见 [docs/steps/02-annotate.md](../docs/steps/02-annotate.md)、[docs/steps/03-html.md](../docs/steps/03-html.md)。 |
| `validate.py` | 相邻 `word-block` 检测（与 [docs/EDITORIAL.md](../docs/EDITORIAL.md) 一致） |
| `paths.py` | 仓库根路径 |
| `build_deploy_site.py` | EdgeOne 专用：生成 **`site/`** 最小静态树（见根目录 **`edgeone.json`**），避免部署包文件数超限 |
| `requirements.txt` | URL 提取与搜索可选依赖 |
| `synth_llm_annotations_lexicon.py` | **非 chat_json 终稿**：keywords 式稀疏占位。`chat_json` 须大模型产出 JSON（不必 Cursor），见 [docs/ANNOTATION.md](../docs/ANNOTATION.md)。 |
| `gen_dense_chat_json.py` | **应急**：词表匹配 + en 去重；**最长 `zh` 优先**；无匹配则该句 `skip`；须对话补全后再当终稿。 |
| `gen_shortest_zh_chat_json.py` | **应急**：同上候选池思路，但 **最短 `zh` 优先**，更贴近「窄锚点」；仍须对话精校。可选 `annotate_lexicon_extra.json` 仅编者明示时使用（见 [docs/ANNOTATION.md](../docs/ANNOTATION.md)）。 |

## 与 `util/` 的分工

- **`util/keyword_lexicon.py`**：全局 `keywords` 词表；**`util/annotate_lib.py`**：标注与页面壳（被本目录 `build_draft.py` 等共用）。
- **`util/crawl-with-playwright.py`**：微信等强反爬页，由 `acquire.py` 在 url 模式下调用。
- **`util/md_split.py`**：Markdown 按空行切段；`build_draft` / `export-chat-bundle` / `synth_*` 共用。
