# MingoX 内容生产流水线（总览）

第一次阅读建议先看 **[docs/README.md](./README.md)**（文档地图）。

编排入口（仓库根目录）：

```bash
python3 workflow/mingox.py --help
```

## 标准路径（唯一）

每篇稿件使用 **`content/drafts/<slug>/`**：`meta.json` 与 `01-source.md` 同目录；正文由 **`mingox acquire`** 写入 MD；默认 **`annotate_engine=chat_json`**（`llm_annotations.json`），可选词表占位见 **`mingox synth-lexicon-annotations`**，终稿以对话产出 JSON 为准。详见 [ANNOTATION.md](./ANNOTATION.md)。

**典型命令**：`mingox init` → `acquire` →（可选）`synth-lexicon-annotations` / `export-chat-bundle` → 对话补全标注 → `build`。

以往的 **`article-profiles.json` + `annotate-wechat-plain.py` + `mingox wechat`** 已移除；旧流程请改为上述草稿目录 + `build`。

## 四步索引（分步详述）

**标注约定**：全仓库**默认 `chat_json`**；`keywords` **仅当编者对某篇单独明确要求**时使用（见 [ANNOTATION.md](./ANNOTATION.md) 文首）。

| 步 | 文档 | 一句话 |
|----|------|--------|
| 1 素材获取 | **[docs/steps/01-acquire.md](./steps/01-acquire.md)** | `init` / `acquire` → `01-source.md` + `meta.json` |
| 2 标注 | **[docs/steps/02-annotate.md](./steps/02-annotate.md)** | **默认 `chat_json`**；或（仅编者要求时）`keywords`（[util/keyword_lexicon.py](../util/keyword_lexicon.py)）；见 [ANNOTATION.md](./ANNOTATION.md) |
| 3 HTML 成稿 | **[docs/steps/03-html.md](./steps/03-html.md)** | `build` → `posts/*.html`，`validate`，DOM/CSS 契约 |
| 4 发布 | **[docs/steps/04-publish.md](./steps/04-publish.md)** | `serve`、`deploy`、Gitee Pages |

**分步目录索引**：[docs/steps/README.md](./steps/README.md)。**标注总览与决策树**：[ANNOTATION.md](./ANNOTATION.md)。**草稿目录与词表细则**：[content/drafts/README.md](../content/drafts/README.md)。

**可选代码层解耦（IR / 拆分 build）**：[docs/steps/IR-ROADMAP.md](./steps/IR-ROADMAP.md)（未实现，待评审）。

---

## 目录职责（速查）

| 路径 | 职责 |
|------|------|
| **`content/drafts/<slug>/`** | 单篇草稿：`01-source.md`、`meta.json`；`build` 后 `02-annotate-tasks.json`；`chat_json` 时维护 `llm_annotations.json` 等 |
| **`workflow/`** | `mingox.py`：`init`、`acquire`、`build`、`validate`、`serve`、`deploy` 等 |
| **`util/keyword_lexicon.py`** | 全局默认可标注词表（`annotate_engine=keywords`） |
| **`util/annotate_lib.py`** | 段落标注、`word-block` 渲染、词汇表、`build_post_html`（`KEYWORDS` 来自 `keyword_lexicon`） |
| **`util/annotate_merge.py`** | `chat_json` 对话 JSON 合并与校验 |
| **`util/.crawl-output/`** | 本地抓取缓存（gitignore） |
| **`posts/`** | 成稿静态 HTML |
| **`docs/`** | 文档地图 [README.md](./README.md)、[PIPELINE.md](./PIPELINE.md)、[EDITORIAL.md](./EDITORIAL.md)、[ANNOTATION.md](./ANNOTATION.md)、四步分册、[PREREQUISITES.md](./PREREQUISITES.md) |

---

## 环境与其它说明

- **依赖安装**： [PREREQUISITES.md](./PREREQUISITES.md)
- **抓取与 Playwright 细节**： [util/README.md](../util/README.md)
- **版式、词汇规范全文**： [EDITORIAL.md](./EDITORIAL.md)
- **workflow 模块表**： [workflow/README.md](../workflow/README.md)

---

## 与 EDITORIAL / 根 README 的关系

- **列表、标题、词汇、相邻块、外源版权块等编辑规范**：以 [EDITORIAL.md](./EDITORIAL.md) 为权威；根 [README.md](../README.md) 为项目门面与快速链接。
- **本文件与 `docs/steps/`**：约定**步骤边界与命令入口**，避免与 `util/`、草稿职责混淆。
