# 🎙️ MingoX

**Multimedia Post in Mixed Languages**

多语言多媒体内容平台 —— 用文字、图片、播客等多种形式，分享新闻、思想与见解。

## 🌐 在线访问

- **Gitee Pages**: https://siglea.gitee.io/news

## 🎯 核心理念

| 维度 | 说明 |
|------|------|
| **M - Mixed Languages** | 中英等多语言混合表达，跨越语言边界 |
| **X - Multimedia** | 文字、图片、播客等多元形式，X 代表无限可能 |
| **News & Ideas** | 新闻、思想、见解的交汇与碰撞 |

**形式**：文字 / 图片 / 播客 / 视频。**语言**：中英混排，正文可标重点词（见下「词汇标注」）。

## 📁 目录结构

```
news/
├── index.html          # 首页/内容列表
├── about.html          # 关于页面
├── _config.yml         # Gitee Pages 配置
├── README.md           # 项目说明
├── .gitignore          # Git 忽略文件
├── css/
│   └── style.css       # 公共样式
├── js/
│   └── main.js         # 公共脚本
├── posts/              # 内容目录
│   └── 2026-03-28-us-stock.html
└── images/             # 图片资源
```

## 🎯 内容规范

### 标题与首页

**首页列表标题与文内 `h1` 须完全一致**（仅 `small` 字号首页可用 16px、文内 18px）：

```html
<h1>[emoji] 中文<br><small style="font-size: 18px; color: #888;">English</small></h1>
```

列表项：`post-title` 与 `post-excerpt` **分别**链向文章，`post-meta` 不链；标题链接样式见 `css/style.css`。

### Meta 与摘要

- Meta：`📅 YYYY-MM-DD | 📝 双语 | 🏷️ 标签`（形式：📝🖼️🎙️📹；语言：🌐🇨🇳🇬🇧；主题忌「学习/教程」类）。
- 摘要：一句话新闻/观点价值；例：七巨头蒸发、诉讼致大跌等。

### 词汇标注

**HTML**（须含音标；`english-word` 可为**一个词**或**一个**固定搭配如 `on hold`、`dot plot`、`risk-free`；**勿**拆成两个紧挨的 `word-block`）：

```html
<span class="word-block"><span class="english-word">surged</span><span class="word-info">[sɜːdʒd] v. 激增</span></span>
```

**选取与密度**：跳过专名；**不标**日常极简单词 + 高中课标常见无生僻义项词（如 get、market、price、gold、chain…），**不拿它们凑密度**。优先考研/新闻书面语与财经科技机制词（如 hawkish、leverage、ETF、monetization）。**段落内**约每 1～2 句（以 `。？！；` 分句，英文导语 `;` 可分句）**至少 1 处**；若无可标英文，可做**中文 → 英文词/单一搭配**替换，**不改事实与论点**。供应链语义用 **logistics** 等上位词，**不单标 chain**。

**叙事**：避免「中文已说清动作再叠近义英文」（例：不宜 `pause`+「暂停降息」→ 可用 `on hold`+短补足语）。混排里的英文碎片须**全部**进 `word-block` 与词汇表。

**相邻**：仅当两 `word-block` 的 `</span></span>` 与下一 `<span class="word-block"` 之间**仅有空白**才算违规；中间有中文/标点即合规。不可分割的搭配请**整块**写进一个 `word-block`。

**词汇表**：与正文标注**词形一一对应**（同形只列一行）；`</thead>` 后须有 **`<tbody>`**。

**范文**：`posts/2026-03-29-china-g7-europe-market.html`（政经）；`posts/2026-03-29-gold-price-analysis.html`（利率/贵金属密度与固定搭配写法）。

**自检（零输出为通过）**：`rg '</span></span>\s+<span class="word-block"' posts/`

## 🚀 添加新内容

1. `posts/YYYY-MM-DD-title.html`，结构同现有文章：`../css/style.css`、`../js/main.js`，文内 `h1` 与首页列表标题一致。
2. 在 `index.html` 增加列表项。
3. `git add` → `commit` → `push`。

## 🛠️ 部署（Gitee Pages）

仓库 → 服务 → Gitee Pages → 选分支与根目录 `/` → 启动；域名见仓库 Pages 说明。

## 📄 许可证

MIT License
