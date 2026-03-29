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

**重要原则：首页列表标题必须与 post 文件内的 h1 标题保持一致**

post 文件 h1 标题格式：
```html
<h1>[emoji] 中文标题<br><small style="font-size: 18px; color: #888;">English Title</small></h1>
```

首页列表标题格式（与 post 文件一致）：
```
[emoji] 中文标题<br><small style="font-size: 16px; color: #888;">English Title</small>
```

- 使用 emoji 表示内容类型：📈 新闻、💡 思想、🎙️ 播客 等
- 中文主标题 + 英文副标题（small 标签包裹）
- **严格保持首页与文章页标题一致**，避免用户困惑

### 首页列表设计规范

**每个条目（cell）必须整体可点击：**

```html
<li class="post-item">
    <a href="posts/YYYY-MM-DD-title.html" class="post-link">
        <div class="post-title">
            [emoji] 中文标题<br>
            <small style="font-size: 16px; color: #888;">English Title</small>
        </div>
        <div class="post-meta">📅 YYYY-MM-DD | 📝 双语 | 🏷️ 标签</div>
        <div class="post-excerpt">摘要内容...</div>
    </a>
</li>
```

**关键要求：**
- 整个 `li.post-item` 使用 `<a>` 标签包裹，使标题、meta、摘要区域整体可点击
- 标题必须分行显示：emoji+中文标题一行，英文副标题一行（使用 `<br>` 换行）
- 英文副标题使用 `<small>` 标签，字号 16px，颜色 #888

**链接样式规范（悬浮才出现）：**
- 默认状态：标题颜色与普通文字一致（`var(--text-color)`），无下划线
- 悬浮状态：标题变色为主题色（`var(--primary-color)`），可以添加下划线
- 实现方式：使用 CSS 的 `:hover` 伪类控制样式变化

```css
.post-link {
    display: block;
    color: inherit;
    text-decoration: none;
}

.post-link .post-title {
    color: var(--text-color);
}

.post-link:hover .post-title {
    color: var(--primary-color);
}
```

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

### 词汇标注规范

- 被识别的英文单词使用 `<span class="word-block">` 包裹，包含单词和音标释义
- **严格禁止**：连续标注紧挨着的单词（如 "capital market"、"risk aversion" 等相邻词汇不能同时标注）
- **只允许单个单词**：不要标注词组或短语，只选择最核心的那个单词进行标注
- **间隔原则**：两个被标注的单词之间，必须有至少一个未标注的单词或标点符号隔开
- 优先标注**核心动词、形容词、关键名词**，跳过专有名词（如 Steve Jobs、Android 等）

#### 连续标注示例（❌ 错误）

```html
<!-- 错误：capital 和 market 紧挨着，解释会重叠 -->
<span class="word-block"><span class="english-word">capital</span>...</span>
<span class="word-block"><span class="english-word">market</span>...</span>

<!-- 错误：stock 和 price 之间没有间隔 -->
<span class="word-block"><span class="english-word">stock</span>...</span>
<span class="word-block"><span class="english-word">price</span>...</span>
```

#### 正确示例（✅ 正确）

```html
<!-- 正确：只标注最核心的单词 market -->
<span class="word-block"><span class="english-word">market</span><span class="word-info">[ˈmɑːkɪt] n. 市场</span></span>

<!-- 正确：surged 和 evaporated 之间有其他内容隔开 -->
<span class="word-block"><span class="english-word">surged</span><span class="word-info">[sɜːdʒd] v. 激增</span></span>近50倍...累计
<span class="word-block"><span class="english-word">evaporated</span><span class="word-info">[ɪˈvæpəreɪtɪd] v. 蒸发</span></span>超过...
```

#### 技术实现约束

词汇标注必须使用以下 HTML 结构，否则样式无法正常显示：

```html
<span class="word-block">
    <span class="english-word">单词</span>
    <span class="word-info">[音标] 词性. 释义</span>
</span>
```

**错误示例（旧格式，不要再用）：**
```html
<!-- 错误：没有 word-block 包裹 -->
<span class="english-word">单词</span><span class="word-info">（词性.释义）</span>

<!-- 错误：没有音标 -->
<span class="word-block"><span class="english-word">单词</span><span class="word-info">n. 释义</span></span>
```

**正确示例：**
```html
<span class="word-block"><span class="english-word">surged</span><span class="word-info">[sɜːdʒd] v. 激增</span></span>
```

#### 词汇表格式

词汇表必须包含**音标列**，表头格式：
```html
<thead>
    <tr><th>词汇</th><th>音标</th><th>词性</th><th>释义</th></tr>
</thead>
```

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
            <h1>[emoji] 中文标题<br><small style="font-size: 18px; color: #888;">English Title</small></h1>
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
