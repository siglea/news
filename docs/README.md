# 文档地图

第一次 clone 仓库建议先读本页，再按**角色**跳转。

## 📚 按职能（文件名 = 维度）

| 文档 / 目录 | 职能 |
|-------------|------|
| **[GETTING-STARTED.md](./GETTING-STARTED.md)** | 装环境 + 第一篇 walkthrough + `make test`/`ci` 入口 |
| **[TOOLING.md](./TOOLING.md)** | **`mingox` CLI**、目录职责、四步索引、harness 中立约定 |
| **[PLAYBOOK.md](./PLAYBOOK.md)** | **协作与审发**：claim、先审后发、发布前清单、deploy 串行 |
| **[EDITORIAL.md](./EDITORIAL.md)** | 标题、首页列表、摘要、外源版权等**编辑规范**（版式为主） |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | 未来可选：标注 IR / 拆分 build（**非当前必读**） |
| **[steps/](./steps/README.md)** | 第 1～4 步**分册**；每篇文首标明为 TOOLING 的展开 |

## 按角色

| 你是谁 | 建议阅读顺序 |
|--------|----------------|
| **访客 / 读者** | 仓库根目录 [README.md](../README.md) |
| **新同学：装环境 + 跑通一篇** | [GETTING-STARTED.md](./GETTING-STARTED.md) → [TOOLING.md](./TOOLING.md) → [steps/README.md](./steps/README.md) |
| **执行位（发稿）** | [TOOLING.md](./TOOLING.md) + [steps/](./steps/README.md)；节奏见 [PLAYBOOK.md](./PLAYBOOK.md) |
| **审核位** | [PLAYBOOK.md](./PLAYBOOK.md) + [EDITORIAL.md](./EDITORIAL.md) |
| **内容编辑 / 版式** | [EDITORIAL.md](./EDITORIAL.md)；标注细节 [steps/02-annotate.md](./steps/02-annotate.md) |
| **改脚本、util** | [GETTING-STARTED.md](./GETTING-STARTED.md)；[workflow/README.md](../workflow/README.md)、[util/README.md](../util/README.md) |

## 核心文件索引

| 文档 | 内容 |
|------|------|
| [TOOLING.md](./TOOLING.md) | `mingox.py` 入口、**目录职责速查**、四步索引 |
| [PLAYBOOK.md](./PLAYBOOK.md) | 协作、审发、清单、deploy 约定 |
| [GETTING-STARTED.md](./GETTING-STARTED.md) | 依赖、`make ci`、最小闭环 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | IR / 拆分路线图（待评审） |
| [steps/README.md](./steps/README.md) | 分步文档入口 |
| [EDITORIAL.md](./EDITORIAL.md) | 编辑规范全文 |
| [content/drafts/README.md](../content/drafts/README.md) | 草稿目录与 `meta.json` |
| [workflow/README.md](../workflow/README.md) | `workflow/` 模块表 |
| [util/README.md](../util/README.md) | 抓取、`annotate_lib` |

命令与边界的**权威展开**在 [TOOLING.md](./TOOLING.md) 与各 `steps/*.md`；本页不重复四步长表。
