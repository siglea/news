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

## 一键部署（EdgeOne，推荐）

```bash
python3 workflow/mingox.py deploy --project mingox
```

若希望按固定顺序跑完整闭环，推荐先用：

```bash
python3 workflow/mingox.py close-loop --slug <slug> --deploy
```

该命令会先执行 `build -> validate`，通过后再 `deploy`。

- 依赖：**Node** + `npx` 拉取 EdgeOne CLI；身份可用 **登录** 或 **Token**。
- Token 可置于 **`.edgeone/.token`**（勿提交密钥；`.gitignore` 已忽略）。

**环境与其它工具**：[PREREQUISITES.md](../PREREQUISITES.md)。

---

## Gitee Pages

1. 推送代码到 Gitee 仓库
2. 进入 Gitee 仓库页面 → 服务 → Gitee Pages
3. 选择部署分支（master/main）和部署目录（根目录 `/`）
4. 点击「启动」按钮
5. 等待部署完成，访问分配的域名

站点配置见仓库根目录 **`_config.yml`**。**在线地址示例**见根 [README.md](../../README.md)「在线访问」。

---

## EdgeOne Pages（CLI 细则）

本项目为**纯静态站点**（根目录 `index.html` + `posts/` + `css/` + `js/`），可用 [EdgeOne Pages](https://pages.edgeone.ai/) 官方 CLI 部署。更完整的代理说明见官方 Skill：[edgeone-pages-skills](https://github.com/edgeone-pages/edgeone-pages-skills)。

### 本仓库约定

| 项 | 约定 |
|----|------|
| **EdgeOne 项目名** | 固定为 **`mingox`**（与远程已有项目同名时，CLI 会**复用该项目并上传新版本**） |
| **部署区域** | **中国站**使用 **`-a overseas`**（`pages deploy` 的 `area` 参数；勿与「国际站 `-a global`」混用） |
| **敏感信息** | API Token **仅放本地** `.edgeone/.token`（单行）；**勿提交**到 Git |
| **构建输出** | **[edgeone.json](../../edgeone.json)**：`buildCommand` 为空，`outputDirectory` 为 **`.`**（**仓库根**即静态站点根）。不再生成 **`site/`**。若远程构建报 **文件数量超限**，可在 EdgeOne 控制台调整忽略/包含规则，或另行增加仅复制静态资源的脚本。 |

### 环境要求

- Node.js ≥ 16、npm
- CLI **≥ 1.2.30**（执行 `edgeone -v` 或下文 `npx` 时查看横幅版本）

### 推荐：用 `npx` 调用 CLI（免全局安装）

在 macOS/Linux 上，`npm install -g` 常因目录权限失败（`EACCES`）。**推荐不装全局包**，在仓库根目录始终用：

```bash
npx --yes edgeone@latest -v
```

### 认证方式（二选一）

**A. 浏览器登录（本机有图形界面时）**

```bash
cd /path/to/news
npx --yes edgeone@latest login --site china
```

按提示在浏览器完成腾讯云账号授权。之后可直接部署（CLI 会把登录态写在用户目录，**不是**必须从 `.token` 读取）。

**B. API Token（适合新电脑、CI、或不想走浏览器登录）**

1. 打开 [EdgeOne Pages 控制台（中国）](https://console.cloud.tencent.com/edgeone/pages) → **设置** → **API Token** → 创建并复制令牌。
2. 在仓库根目录创建 **`.edgeone/.token`**，文件内**仅一行**，粘贴令牌，保存。
3. 部署时用 **`-t`** 传入（可用下面「一键命令」从文件读取，避免把 token 写进 shell 历史）。

**勿**将 token 写入 `README`、issue、或提交进仓库。

### 在项目根目录发布（中国站 + 项目名 mingox）

**使用 `.edgeone/.token`（推荐写入方式，便于换机器）：**

```bash
cd /path/to/news
TOKEN=$(tr -d '\n\r' < .edgeone/.token)
npx --yes edgeone@latest pages deploy -a overseas -n mingox -t "$TOKEN"
```

**已在本机浏览器登录、且无 token 文件时：**

```bash
cd /path/to/news
npx --yes edgeone@latest pages deploy -a overseas -n mingox
```

说明：

- 远程**已存在**名为 `mingox` 的项目时，CLI 会提示使用已有项目并继续上传，**无需**先删云端项目。
- 首次成功后，本地 `.edgeone/project.json` 会记录 `Name` / `ProjectId`（该目录默认被 git 忽略，换电脑后只要重新登录或放好 `.token`，仍用同上命令即可）。

### 部署成功后

`python3 workflow/mingox.py deploy` 结束时**固定打印**两行：**「预览地址（…）」** 与下一行的**完整 https URL**（与 `EDGEONE_DEPLOY_URL=...` 同源，须含 `eo_token` 等参数）。

终端亦会打印 **`EDGEONE_DEPLOY_URL=...`**（可与「预览地址」行互相核对）。

> **必须完整复制含 `?` 及之后全部查询参数的 URL** 访问预览。截断链接（去掉 `?eo_token=...` 部分）会导致页面无法打开或返回 404。
>
> 正确：`https://mingox-xxx.edgeone.cool?eo_token=xxx&eo_time=xxx`
> 错误：`https://mingox-xxx.edgeone.cool`（缺少 token 参数）

可同时打开 CLI 给出的控制台部署详情链接排查构建与访问权限。**私有站点与 token 要求**见根 [README.md](../../README.md)「在线访问」。

### 发布复盘清单

- 回复部署结果时，必须回传**完整预览链接**（包含 `https://` 与 `?` 后所有参数）。
- 不要只发域名；缺少 `eo_token`/`eo_time` 参数时，预览常会无法访问。
- 预览链接含访问令牌，应视为敏感信息，仅在必要范围内传递。

### 可选：全局安装 CLI

若本机允许全局写入：

```bash
npm install -g edgeone@latest
edgeone -v
```

之后将上文命令中的 `npx --yes edgeone@latest` 换成 `edgeone` 即可。

### 纯静态与全栈

纯静态站点**无需**执行 `edgeone pages init`（该命令面向 Edge Functions / Node Functions 等全栈能力）。

### 本地联调（可选）

```bash
npx --yes edgeone@latest pages dev
```

默认示例：<http://localhost:8088/>

---

## 回溯前序步骤

| 步 | 文档 |
|----|------|
| 成稿 HTML 与校验 | [03-html.md](./03-html.md) |
| 标注 | [02-annotate.md](./02-annotate.md) |
| 取材 | [01-acquire.md](./01-acquire.md) |
