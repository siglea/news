# MingoX 内容生产流水线（总览）

第一次阅读建议先看 **[docs/README.md](./README.md)**（文档地图）。

编排入口（仓库根目录）：

```bash
python3 workflow/mingox.py --help
```

## 标准路径

每篇稿件使用 **`content/drafts/<slug>/`**：`meta.json` 与 `01-source.md` 同目录；正文由 **`mingox acquire`** 写入 MD；**`mingox build`** 将 Markdown 段落转为成稿 HTML（当前**不**注入词汇标注；篇末「重点词汇」表可为空，直至新标注模块接入）。详见 [content/drafts/README.md](../content/drafts/README.md)。

**典型命令**：`mingox init` → `acquire` →（可选）`export-chat-bundle` → 保存 `llm_annotations.json` → `build`。

以往的 **`article-profiles.json` + `annotate-wechat-plain.py` + `mingox wechat`** 已移除；旧流程请改为上述草稿目录 + `build`。

## 四步索引（分步详述）

| 步 | 文档 | 一句话 |
|----|------|--------|
| 1 素材获取 | **[docs/steps/01-acquire.md](./steps/01-acquire.md)** | `init` / `acquire` → `01-source.md` + `meta.json` |
| 2 标注 | **[docs/steps/02-annotate.md](./steps/02-annotate.md)** | 四六级向提示词 + `llm_annotations.json`；无则 `build` 仅排版 |
| 3 HTML 成稿 | **[docs/steps/03-html.md](./steps/03-html.md)** | `build` → `posts/*.html`，`validate`，DOM/CSS 契约 |
| 4 发布 | **[docs/steps/04-publish.md](./steps/04-publish.md)** | `serve`、`deploy`、Gitee Pages |

**分步目录索引**：[docs/steps/README.md](./steps/README.md)。**编辑规范**：[EDITORIAL.md](./EDITORIAL.md)。**草稿目录**：[content/drafts/README.md](../content/drafts/README.md)。

**可选代码层解耦（IR / 拆分 build）**：[docs/steps/IR-ROADMAP.md](./steps/IR-ROADMAP.md)（未实现，待评审）。

---

## 目录职责（速查）

| 路径 | 职责 |
|------|------|
| **`content/drafts/<slug>/`** | 单篇草稿：`01-source.md`、`meta.json`；`build` 后 `02-annotate-tasks.json` |
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
