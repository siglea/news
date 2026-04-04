# 内容生产四步（分步文档）

每步单独一篇，避免与总览重复堆叠。**编排入口**仍为仓库根目录：

```bash
python3 workflow/mingox.py --help
```

| 步 | 文档 | 职责摘要 |
|----|------|----------|
| 1 | [01-acquire.md](./01-acquire.md) | `init` / `acquire` → `01-source.md` + `meta.json` |
| 2 | [02-annotate.md](./02-annotate.md) | **默认 `chat_json`**；或 `keywords`（全局词表）；真源与语义约定 |
| 3 | [03-html.md](./03-html.md) | `build` 成稿 HTML 结构、`word-block` DOM 契约、校验 |
| 4 | [04-publish.md](./04-publish.md) | 本地预览、EdgeOne / Gitee 发布 |

**总览与目录表**：[PIPELINE.md](../PIPELINE.md)。**环境依赖**：[PREREQUISITES.md](../PREREQUISITES.md)。

**未来可选（代码层解耦）**：[IR-ROADMAP.md](./IR-ROADMAP.md)（标注中间表示与拆分 `annotate` / `render`，待评审后实现）。
