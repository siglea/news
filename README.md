# 📚 英语学习新闻博客

通过阅读真实新闻来学习英语的静态博客，基于 Gitee Pages 构建。

## 🌐 在线访问

- **Gitee Pages**: https://siglea.gitee.io/news

## 🎯 项目特点

- **真实新闻语境** - 通过时事新闻学习英语词汇
- **单词高亮标注** - 重点单词突出显示，附带词性和释义
- **词汇表复习** - 每篇文章附带完整词汇表，支持搜索功能
- **响应式设计** - 适配桌面和移动设备
- **无需后端** - 纯静态 HTML + CSS + JavaScript

## 📁 目录结构

```
news/
├── index.html          # 首页/文章列表
├── about.html          # 关于页面
├── _config.yml         # Gitee Pages 配置
├── README.md           # 项目说明
├── .gitignore          # Git 忽略文件
├── css/
│   └── style.css       # 公共样式
├── js/
│   └── main.js         # 公共脚本
├── posts/              # 文章目录
│   └── 2026-03-28-us-stock.html
└── images/             # 图片资源
```

## 📝 添加新文章

1. 在 `posts/` 目录创建新 HTML 文件，命名格式：`YYYY-MM-DD-title.html`

2. 参考模板结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>文章标题 | 英语学习博客</title>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar">...</nav>

    <!-- 文章内容 -->
    <main class="main-content">
        <div class="container">
            <div class="card">
                <article class="post-content">
                    <h1>文章标题</h1>
                    <!-- 使用 <span class="english-word">单词</span><span class="word-info">（释义）</span> 标注词汇 -->
                </article>
                <div class="subtitle">📖 词汇表</div>
                <table class="vocab-table">...</table>
            </div>
        </div>
    </main>

    <!-- 页脚 -->
    <footer class="footer">...</footer>
    <script src="../js/main.js"></script>
</body>
</html>
```

3. 在 `index.html` 的文章列表中添加新文章链接

4. 提交并推送：

```bash
git add .
git commit -m "添加新文章：标题"
git push
```

## 🚀 部署到 Gitee Pages

1. 推送代码到 Gitee 仓库

2. 进入 Gitee 仓库页面 → 服务 → Gitee Pages

3. 选择部署分支（master）和部署目录（根目录 `/`）

4. 点击「启动」按钮

5. 等待部署完成，访问分配的域名

## 🛠️ 技术栈

- **静态站点生成**: 原生 HTML (可选 Jekyll)
- **样式**: CSS3 (CSS Variables, Flexbox, Gradient)
- **交互**: 原生 JavaScript (ES5 for compatibility)
- **托管**: Gitee Pages

## 📄 许可证

MIT License
