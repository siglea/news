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

**标题和内容分别添加超链接：**

```html
<li class="post-item">
    <div class="post-title">
        <a href="posts/YYYY-MM-DD-title.html">
            [emoji] 中文标题<br>
            <small style="font-size: 16px; color: #888;">English Title</small>
        </a>
    </div>
    <div class="post-meta">📅 YYYY-MM-DD | 📝 双语 | 🏷️ 标签</div>
    <div class="post-excerpt">
        <a href="posts/YYYY-MM-DD-title.html">
            摘要内容...
        </a>
    </div>
</li>
```

**关键要求：**
- 标题（`post-title`）和内容（`post-excerpt`）分别添加超链接
- Meta 信息（日期、标签）**不添加**超链接
- 标题必须分行显示：emoji+中文标题一行，英文副标题一行（使用 `<br>` 换行）
- 英文副标题使用 `<small>` 标签，字号 16px，颜色 #888

**链接样式规范（悬浮才出现）：**
- 默认状态：标题颜色与普通文字一致（`var(--text-color)`），无下划线
- 悬浮状态：标题变色为主题色（`var(--primary-color)`），可以添加下划线
- 实现方式：使用 CSS 的 `:hover` 伪类控制样式变化

```css
.post-title a {
    color: var(--text-color);
    text-decoration: none;
}

.post-title a:hover {
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
- **只允许单个单词**：不要标注词组或短语，只选择最核心的那个单词进行标注
- 优先标注**核心动词、形容词、关键名词**，跳过专有名词（如 Steve Jobs、Android 等）

#### 哪些词可以 / 不应被识别（选取原则）

1. **不识别**：非常简单的词（如 yes、good、big、get、make、close、drop 等日常高频基础词），除非在文中构成专业义项且属于下一条范围。
2. **不识别**：中国普通高中英语课程标准范围内、无生僻义项的常见词（如 price、risk、trade、market、meeting、international、demand、flow、cancel 等）。**不确定时宁可少标。**
3. **优先识别**：涉及文章**关键信息、因果、立场、数据判断**的英文词（如 warning、closure、hawkish、sanctions、valuation、hedge、materialize 等）。
4. **密度**：在**同一自然段内**，大致每 1～2 句至少出现 **1 处** `word-block`（以中文句读为准）；**若该句及相邻句完全没有可标的英文，或仅有品牌/专名，则不强行凑数**——不得为此改写、增删正文。
5. **优先识别**：考研英语大纲及真题阅读中**常见、重要的动词与名词**（如 surge、plunge、evaporate、decompose、sanctions、paradox、speculator、inflation、valuation 等），以及财经/科技语篇中的**学科常用词**（如 token、ETF、GPU、architecture、monetization）。

**词汇表**须与正文中的 `word-block` **一一对应**，只收录正文中实际标注的词。


#### 「相邻 word-block」的严格定义（必读）

两个 `word-block` **视为相邻**，当且仅当：前一个 `word-block` 的结束标记 `</span></span>` 与后一个 `<span class="word-block"` 之间**只有空白**（空格、换行、制表符），**没有任何其他字符**（包括英文单词、中文、标点）。

- **违规**：`</span></span> <span class="word-block"`（中间只有空格/换行）
- **合规**：`</span></span>问题，系统自动<span class="word-block"`（中间有中文）
- **合规**：`capital <span class="word-block"`（前一个英文词未加标注，与标注块之间有空格——空格左侧是未标注的英文，不是第二个 word-block）

**同一英文短语拆成两个标注**（如 gold price、safe haven、short position）一律按「相邻」处理，只能保留其中一个 `word-block`，另一个词保持纯文本。

#### 提交前自检（命令）

在仓库根目录执行，**无匹配输出**表示未发现相邻 `word-block`：

```bash
# 已安装 ripgrep 时
rg '</span></span>\s+<span class="word-block"' posts/

# 或仅用 grep
grep -rE '</span></span>[[:space:]]+<span class="word-block"' posts/*.html
```

若命中行，必须修改正文后再提交。可将此命令写入 CI 或本地 git hook。

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
