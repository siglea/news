# 第 4 步：本地预览与多平台发布

**输入**：仓库根目录下的静态站点（`index.html`、`posts/*.html`、`css/`、`js/`、`images/` 等）。

---

## 本地预览

```bash
python3 workflow/mingox.py serve --port 8765
# 默认绑定 127.0.0.1
```

等价于在仓库根运行静态 HTTP 服务，便于本机检查成稿。

---

## EdgeOne Pages

```bash
python3 workflow/mingox.py deploy --project mingox
```

- 依赖：**Node** + `npx` 拉取 EdgeOne CLI；身份可用 **登录** 或 **Token**。
- Token 可置于 **`.edgeone/.token`**（勿提交密钥到公开仓库；确保 `.gitignore` 已忽略）。
- 部署成功后 CLI 可能输出带 `eo_token` 等参数的预览 URL；**分享时需完整复制**（私有站点常见 401 见根 README 说明）。

**环境与其它工具**：[PREREQUISITES.md](../PREREQUISITES.md)。

---

## Gitee Pages

由仓库根 **`_config.yml`** 与 Gitee 仓库设置托管静态页；**在线访问**等说明见根 **[README.md](../../README.md)**「在线访问」一节。

---

## 回溯前序步骤

| 步 | 文档 |
|----|------|
| 成稿 HTML 与校验 | [03-html.md](./03-html.md) |
| 标注 | [02-annotate.md](./02-annotate.md) |
| 取材 | [01-acquire.md](./01-acquire.md) |
