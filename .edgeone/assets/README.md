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

## 📝 内容形式 X

- **📝 文字 (Text)** - 深度文章、新闻快讯、思想随笔
- **🖼️ 图片 (Image)** - 信息图表、视觉故事、摄影作品
- **🎙️ 播客 (Podcast)** - 音频节目、对话访谈、有声内容
- **📹 视频 (Video)** - 短视频、纪录片、直播回放

## 🌍 语言特色

- 中英双语对照呈现，保留原文语境
- 标注重点词汇与表达，便于理解
- 多语言内容并行，满足不同读者需求

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

### 标题格式

首页文章列表标题统一格式：
```
[emoji] 中文标题 | English Title
```

- 使用 emoji 表示内容类型：📈 新闻、💡 思想、🎙️ 播客 等
- 中英文标题用 `|` 分隔
- 简洁明了，突出核心信息

### 标签规范

文章 meta 信息格式：
```
📅 YYYY-MM-DD | 📝 双语 | 🏷️ 标签1, 标签2
```

- **内容形式**：📝 文字、🖼️ 图片、🎙️ 播客、📹 视频
- **语言类型**：🌐 多语言、🇨🇳 中文、🇬🇧 英文
- **主题标签**：财经、科技、文化、观点 等（不用"学习""教程"等教育类标签）

### 摘要规范

- 一句话概括内容核心
- 突出新闻/观点价值，而非"学习价值"
- 示例："美股七巨头市值蒸发超8500亿美元，Meta因诉讼案暴跌11%"

## 🚀 添加新内容

1. 在 `posts/` 目录创建新 HTML 文件，命名格式：`YYYY-MM-DD-title.html`

2. 参考模板结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>中文标题 | English Title | MingoX</title>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <nav class="navbar">...</nav>
    <main class="main-content">
        <article class="post-content">
            <h1>[emoji] 中文标题 | English Title</h1>
            <!-- 双语内容，保留词汇标注 -->
        </article>
    </main>
    <footer class="footer">...</footer>
    <script src="../js/main.js"></script>
</body>
</html>
```

3. 在 `index.html` 的内容列表中添加新链接

4. 提交并推送：

```bash
git add .
git commit -m "添加新内容：标题"
git push
```

## 🛠️ 部署到 Gitee Pages

1. 推送代码到 Gitee 仓库
2. 进入 Gitee 仓库页面 → 服务 → Gitee Pages
3. 选择部署分支（master/main）和部署目录（根目录 `/`）
4. 点击「启动」按钮
5. 等待部署完成，访问分配的域名

## 📄 许可证

MIT License
