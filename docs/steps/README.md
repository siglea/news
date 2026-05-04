# 内容生产四步（分步文档）

**定位**：本目录是 [TOOLING.md](../TOOLING.md) 的**四步展开**；总览、目录职责与 harness 约定以 TOOLING 为准。

**编排入口**（仓库根目录）：

```bash
python3 workflow/mingox.py --help
```

**四步总览、目录职责速查**：[TOOLING.md](../TOOLING.md)。**文档地图**：[../README.md](../README.md)。**环境**：[GETTING-STARTED.md](../GETTING-STARTED.md)。

| 步 | 文档 |
|----|------|
| 1 | [01-acquire.md](./01-acquire.md) |
| 2 | [02-annotate.md](./02-annotate.md) |
| 3 | [03-html.md](./03-html.md) |
| 4 | [04-publish.md](./04-publish.md) |

各步内的命令、边界与示例以对应文件为准；本页不重复「一句话职责」表（见 TOOLING）。

**未来可选（代码层解耦）**：[ARCHITECTURE.md](../ARCHITECTURE.md)（标注 IR 与拆分 `annotate` / `render`，待评审后实现）。
