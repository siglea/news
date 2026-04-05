# 前置环境（内容流水线）

完成 [PIPELINE.md](./PIPELINE.md) / [docs/steps/](./steps/README.md) 四步前，请在本机准备：

## Git

- 安装 Git，仓库克隆后用于版本管理与提交 `posts/`、`index.html` 等。

## Python

- 建议 **Python 3.10+**。
- 微信抓取（Playwright）：

```bash
pip3 install -r util/requirements-crawl.txt
python3 -m playwright install chromium
```

- 流水线第 1 步（普通网页 URL、DuckDuckGo 检索，可选）：

```bash
pip3 install -r workflow/requirements.txt
```

## Node.js 与 EdgeOne（第 4 步部署）

- **Node.js ≥ 16**、npm。
- 中国站部署见 [docs/steps/04-publish.md](./steps/04-publish.md)「EdgeOne Pages（CLI 细则）」：推荐 `npx edgeone@latest pages deploy -a overseas -n mingox`，Token 放 `.edgeone/.token`（勿提交）。一键入口：`python3 workflow/mingox.py deploy`。

## 小结

| 步骤 | 依赖 |
|------|------|
| 1 获取原文 | `workflow/requirements.txt`；微信域名另需 Playwright |
| 2 标注 | `export-chat-bundle` + `llm_annotations.json`（见 steps/02-annotate.md）；可省略 |
| 3 出 HTML | 同上 |
| 4 本地预览 | 仅 Python：`python -m http.server` |
| 4 远程发布 | Node + EdgeOne CLI |
