# 🎙️ MingoX

**Multimedia Post in Mixed Languages** — 多语言多媒体内容平台：中英混排文章、词汇标注与静态站点发布。

> **文档迁移**：原根目录中的长篇**版式、词汇密度、相邻块、外源版权**等规范已迁至 **[docs/EDITORIAL.md](docs/EDITORIAL.md)**。请编辑与校对时以该文件为权威。

## 🌐 在线访问

- **Gitee Pages**: https://siglea.gitee.io/news
- **EdgeOne Pages**（中国站）：部署成功后以 CLI 输出的 `EDGEONE_DEPLOY_URL` 为准（须**完整复制**含 `?eo_token=...` 的 URL，裸域名会 401）。控制台：[EdgeOne Pages](https://console.cloud.tencent.com/edgeone/pages)

## 快速开始

```bash
python3 workflow/mingox.py serve --port 8765
# 浏览器打开 http://127.0.0.1:8765/
```

环境与依赖：[docs/PREREQUISITES.md](docs/PREREQUISITES.md)。**文档地图（按角色指路）**：[docs/README.md](docs/README.md)。

## 流水线与规范

- **四步总览、目录职责、`mingox` 命令**：[docs/PIPELINE.md](docs/PIPELINE.md)
- **第 1～4 步分册索引**：[docs/steps/README.md](docs/steps/README.md)
- **标注引擎与校验分层**：[docs/ANNOTATION.md](docs/ANNOTATION.md)（**默认 `chat_json`**，除非编者对某篇单独要求再用 `keywords`）
- **标题、列表、词汇、版权等编辑规范全文**：[docs/EDITORIAL.md](docs/EDITORIAL.md)
- **单篇草稿目录约定**：[content/drafts/README.md](content/drafts/README.md)
- **抓取与 Playwright**：[docs/steps/01-acquire.md](docs/steps/01-acquire.md)、[util/README.md](util/README.md)

## 目录结构（简）

```
news/
├── docs/           # 文档地图 README、PIPELINE、EDITORIAL、ANNOTATION、steps/
├── workflow/       # mingox.py CLI（见 workflow/README.md）
├── content/drafts/ # 单篇草稿（见 content/drafts/README.md）
├── util/           # 抓取、annotate_lib、keyword_lexicon、annotate_merge（见 util/README.md）
├── posts/          # 成稿 HTML
├── css/ js/ images/
├── index.html about.html
└── _config.yml     # Gitee Pages
```

更完整的**路径职责表**见 [docs/PIPELINE.md](docs/PIPELINE.md)「目录职责」。

## 产品简介

中英双语对照、重点词汇标注；支持文字与后续多媒体形式。核心理念：**M**ixed languages、**X**（Multimedia 等扩展）、News & Ideas。

## 部署

**Gitee Pages、EdgeOne CLI、`mingox deploy` 详述**：[docs/steps/04-publish.md](docs/steps/04-publish.md)。

## 📄 许可证

MIT License
