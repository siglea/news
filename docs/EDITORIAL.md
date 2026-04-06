# MingoX 编辑与内容规范

**HTML/CSS 与成稿 DOM 契约**以 [docs/steps/03-html.md](./steps/03-html.md) 与实现代码为准。本文约定**标题、首页列表、摘要、外源版权块**等编辑与版式规则。历史成稿中若含 `word-block` 与篇末词汇表，DOM 与样式仍由 `css/style.css` 支持；**当前 `mingox build` 不再生成标注**，新流水线接入前正文为纯转义段落。

**流水线**（取材 → build → 发布）：[PIPELINE.md](./PIPELINE.md)。**相邻 `word-block` 自检**（针对已有 HTML）：`mingox validate`。

---

## 标题格式

**原则一（一致）**：首页列表标题必须与 post 内 `h1` **逐字一致**。英文副标题统一用 `<small class="title-en">`，**勿在 HTML 写死字号/颜色**；文内与列表的视觉差异由 `css/style.css` 中 `.post-content h1 .title-en` 与 `.post-title .title-en` 控制。

**原则二（直击核心）**：标题须**简短、清楚**，一句话点出全文**核心事实或主要矛盾**（主体 + 关键动作/数据/后果）。避免泛泛的「大震荡」「周末突发」「XX与YY」等读者看不出要点的题目；英文副标题与中文主标题**信息对齐、语义等价**，不用空洞口号式翻译。

post 文件 h1 标题格式：

```html
<h1>[emoji] 中文标题<br><small class="title-en">English Title</small></h1>
```

首页列表标题格式（与 post 文件一致）：

```
[emoji] 中文标题<br><small class="title-en">English Title</small>
```

- 使用 emoji 表示内容类型：📈 新闻、💡 思想、🎙️ 播客 等
- 中文主标题 + 英文副标题（`small.title-en`）；完稿前对照**原则一、原则二**自检

## 首页列表设计规范

**标题和内容分别添加超链接：**

```html
<li class="post-item">
    <div class="post-title">
        <a href="posts/YYYY-MM-DD-title.html">
            [emoji] 中文标题<br>
            <small class="title-en">English Title</small>
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
- 英文副标题使用 `<small class="title-en">`，样式由全局 CSS 统一，列表与正文 h1 可略有差异（见 `style.css`）

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

## 标签规范

文章 meta 信息格式：

```
📅 YYYY-MM-DD | 📝 双语 | 🏷️ 标签1, 标签2
```

- **内容形式**：📝 文字、🖼️ 图片、🎙️ 播客、📹 视频
- **语言类型**：🌐 多语言、🇨🇳 中文、🇬🇧 英文
- **主题标签**：财经、科技、文化、观点 等（不用"学习""教程"等教育类标签）

## 摘要规范

- 一句话概括内容核心
- 突出新闻/观点价值，而非"学习价值"
- 示例："美股七巨头市值蒸发超8500亿美元，Meta因诉讼案暴跌11%"

## 移动端与排版

- 样式集中在 `css/style.css`：**正文**用 `clamp` 保证手机端约 **16～17px**、行高约 **1.8**；系统字体栈含 **PingFang / 微软雅黑**；`viewport-fit=cover` 与 **safe-area** 留白；若篇末有词汇表，表格外包裹 **`.vocab-table-wrap`** 以便窄屏横向滑动。
- 文章/列表的英文副标题用 **`<small class="title-en">`**，勿写死字号，随主标题缩放。

## 外源素材与版权声明（综述 / 改编稿）

适用于根据**第三方公开内容**（如微信公众号长文、媒体报道等）撰写**要点综述、双语改编或学习向笔记**，而非本站独立采访或一手事实稿。

1. **长版权块仍在文后；文首仅可有一句「出处提示」**：来源、著作权归属、转载规则、原文链接、风险提示等**法律与礼仪性长文**，统一放在 **`</article>` 之后**、**「📖 重点词汇」小标题之前**，与正文在结构上分离；样式上应**醒目**（如边框、底色区分），便于读者一眼看到出处与权利边界。可参考 `posts/2026-04-01-private-fund-ai-hiring-threshold.html` 中的 `post-source-footer` 区块。**经验**：部分读者只扫标题与首段，容易误以为「正文里看不到转载说明」；因此当 `meta.json` 中 **`include_source_footer` 为真**且填写了 **`source_account`** 时，`workflow/build_draft.py` → `util/annotate_lib.build_post_html` 会在 **`<h1>` 与首段 `<p>` 之间**自动插入 **`post-source-banner`**（一句，类名 `post-source-banner`），写明微信公众号名并**指向文末「来源与版权」**。**该横幅不是版权块的替代**，详细权利说明仍以文末 `post-source-footer` 为准。
2. **版权块保持纯说明**：来源与权利段落中**不要**插入 `word-block` 等学习向标注；若历史模板仍含「重点词汇」空表，可保留结构，待新标注流程再接续。
3. **建议写清的事项**：第三方**平台与帐号名**、界面显示的**作者/署名**（若有）、**可点击的原文固定链接**；说明本站条目为**衍生整理**、不代为授权、不主张对原文的权利；商业转载与摘编由使用者自行联系**权利人**；并保留「不构成投资建议 / 法律意见」等**必要免责**（视题材酌定）。
4. **抓取素材**：若简单 HTTP 拉取被风控（如微信「环境异常」），按 [steps/01-acquire.md](./steps/01-acquire.md)、[util/README.md](../util/README.md) 在本机用 Playwright 等工具获取正文后再改编；若使用 Cursor，可额外参考仓库内 `.cursor/rules/web-crawl-playwright-fallback.mdc`（**非运行依赖**）。**改编与抓取不等于取得转载授权**，发布与商用仍须遵守源站规则及著作权法。

## 新稿与首页入口

**推荐路径**：使用 `python3 workflow/mingox.py init` → `acquire` → `build` 生成 `posts/*.html` 并维护 `index.html` 列表，详见 [PIPELINE.md](./PIPELINE.md)。

以下为**手工编写或核对 HTML** 时的结构参考：

1. 在 `posts/` 目录创建新 HTML 文件，命名格式：**`YYYY-MM-DD-<题材 kebab>.html`**。`<题材 kebab>` 为**英文小写、连字符**的可读 slug，**必须由文章中文标题与英文题（`title_zh` / `title_en`）凝练**，与正文主题一致，例如 `dai-yusen-tencent-ai-water-boiling`、`pinduoduo-xinpinmu-supply-chain`。**不要**用流水线占位、`wechat-<文章 id>`、纯 `mp-xxxx` 或与标题无关的串当 `<题材 kebab>`。`meta.json` 里的 **`slug`（`content/drafts/<slug>/`）同样建议以标题为依据**，**推荐**与 `YYYY-MM-DD-` 后的那段 kebab **一致**；若暂时不同，至少应可读、可联想本篇，而非长期依赖无意义 id。详见 [content/drafts/README.md](../content/drafts/README.md)「命名规范」。

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
        <div class="card">
            <article class="post-content">
                <h1>[emoji] 中文标题<br><small class="title-en">English Title</small></h1>
                <!-- 正文 -->
            </article>
            <!-- 外源稿可选：来源与版权块，见「外源素材与版权声明」 -->
            <div class="subtitle">📖 重点词汇</div>
            <!-- 词汇表 ... -->
        </div>
    </main>
    <footer class="footer">...</footer>
    <script src="../js/main.js"></script>
</body>
</html>
```

3. 在 `index.html` 的内容列表中添加新链接（格式见上文「首页列表设计规范」）。

4. 提交并推送：

```bash
git add .
git commit -m "添加新内容：标题"
git push
```
