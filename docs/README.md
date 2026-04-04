# 文档地图

第一次 clone 仓库建议先读本页，再按角色跳转。

## 按角色

| 你是谁 | 建议阅读顺序 |
|--------|----------------|
| **访客 / 读者** | 仓库根目录 [README.md](../README.md)（在线地址、项目简介） |
| **内容编辑 / 写稿** | [EDITORIAL.md](./EDITORIAL.md)（标题、首页列表、词汇密度、相邻块、外源版权）；[ANNOTATION.md](./ANNOTATION.md)（**默认 `chat_json`**，仅编者单独要求时改用 `keywords`）；单篇草稿 [content/drafts/README.md](../content/drafts/README.md) |
| **跑通一篇流水线** | [PIPELINE.md](./PIPELINE.md)（四步总览与目录职责）；分步命令见 [steps/README.md](./steps/README.md) |
| **改脚本、抓取、util** | 环境 [PREREQUISITES.md](./PREREQUISITES.md)；[workflow/README.md](../workflow/README.md)、[util/README.md](../util/README.md)；取材细节 [steps/01-acquire.md](./steps/01-acquire.md) |

## 核心文件索引

| 文档 | 内容 |
|------|------|
| [PIPELINE.md](./PIPELINE.md) | 四步流水线总览、`mingox.py` 入口、**目录职责速查** |
| [steps/README.md](./steps/README.md) | 第 1～4 步文档入口（索引表） |
| [PREREQUISITES.md](./PREREQUISITES.md) | Git、Python、Playwright、Node/EdgeOne 等 |
| [ANNOTATION.md](./ANNOTATION.md) | `chat_json` / `keywords`、真源、校验与 `validate` 分工 |
| [EDITORIAL.md](./EDITORIAL.md) | 版式与词汇等**编辑规范全文** |
| [content/drafts/README.md](../content/drafts/README.md) | `meta.json`、草稿内各文件、`chat_json` 工作流、同位锚定 |
| [workflow/README.md](../workflow/README.md) | `workflow/` 内各 Python 模块 |
| [util/README.md](../util/README.md) | 抓取、段落抽取、`annotate_lib`、微信 profile 捷径 |

流程与命令的**权威展开**在 [PIPELINE.md](./PIPELINE.md) 与各 `steps/*.md`；本页不重复四步命令长表。
