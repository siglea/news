# 🎙️ MingoX

**Multimedia Post in Mixed Languages**

多语言多媒体内容平台 —— 用文字、图片、播客等多种形式，分享新闻、思想与见解。

## 🌐 在线访问

- **Gitee Pages**: https://siglea.gitee.io/news
- **EdgeOne Pages**（中国站）：部署成功后以 CLI 输出的 `EDGEONE_DEPLOY_URL` 为准

> ⚠️ **重要提示：EdgeOne 访问权限设置要求**
> 
> **1. 项目访问权限必须设为「需要身份验证」（私有）**
> - EdgeOne Pages 项目默认访问控制为「需要身份验证」
> - **禁止修改为「公开访问」**，保持私有以确保安全
> 
> **2. 分享链接时必须完整复制带 token 的 URL**
> - EdgeOne 部署成功后输出的 URL 包含查询参数（如 `?eo_token=xxx&eo_time=xxx`）
> - **必须完整复制包括 `?` 及之后的全部内容**
> - 裸链接（无 token）会返回 401 未授权错误
> 
> ✅ 正确示例：`https://mingox-xxx.edgeone.cool?eo_token=abc123&eo_time=123456`
> ❌ 错误示例：`https://mingox-xxx.edgeone.cool`（缺少参数 → 401）
> 
> **3. 每次部署后 token 会更新，必须使用最新输出的链接**
> 
> 控制台管理：[EdgeOne Pages](https://console.cloud.tencent.com/edgeone/pages)

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
├── README.md           # 项目说明（版式与词汇规范以本文为准）
├── .gitignore          # Git 忽略文件
├── docs/               # 流水线与前置环境说明
│   ├── PIPELINE.md     # 四步总览（详述见 docs/steps/）
│   ├── steps/          # 分步：01 取材 → 02 标注 → 03 HTML → 04 发布
│   ├── ANNOTATION.md   # 标注引擎决策树与校验分层
│   └── PREREQUISITES.md # Git / Python / Playwright / EdgeOne 等
├── workflow/           # 流水线入口与脚本（见 workflow/README.md）
│   ├── mingox.py       # CLI：init / acquire / build / validate / serve / deploy
│   └── requirements.txt
├── content/
│   └── drafts/         # 单篇草稿：meta.json、01-source.md、02-annotate-tasks.json
├── css/
│   └── style.css       # 公共样式
├── js/
│   └── main.js         # 公共脚本
├── posts/              # 成稿 HTML
├── util/               # 抓取、annotate_lib、微信 profile 快捷通道（见 util/README.md）
│   ├── annotate_lib.py
│   ├── crawl-with-playwright.py
│   └── article-profiles.json
└── images/             # 图片资源
```

### 内容生产流水线（四步）

**总览与目录表**：[docs/PIPELINE.md](docs/PIPELINE.md)。**环境**：[docs/PREREQUISITES.md](docs/PREREQUISITES.md)。**分步详述**（每步独立一篇）：

| 步 | 文档 | CLI 概要 |
|----|------|----------|
| 1 素材获取 | [docs/steps/01-acquire.md](docs/steps/01-acquire.md) | `mingox init` / `mingox acquire` → `01-source.md` |
| 2 标注 | [docs/steps/02-annotate.md](docs/steps/02-annotate.md) | **默认 `chat_json`**（`export-chat-bundle` → 对话 → `llm_annotations.json`）；或 **`keywords`**（全局词表 [util/keyword_lexicon.py](util/keyword_lexicon.py)，见 [docs/ANNOTATION.md](docs/ANNOTATION.md)） |
| 3 HTML 成稿 | [docs/steps/03-html.md](docs/steps/03-html.md) | `mingox build` → `posts/*.html`；`mingox validate` |
| 4 发布 | [docs/steps/04-publish.md](docs/steps/04-publish.md) | `mingox serve` / `mingox deploy`；Gitee 见上文「在线访问」 |

**索引**：[docs/steps/README.md](docs/steps/README.md)。**可选：标注 IR 与拆分 build**（未实现）：[docs/steps/IR-ROADMAP.md](docs/steps/IR-ROADMAP.md)。

**对话标注与同位锚定**：[content/drafts/README.md](content/drafts/README.md)（主路径 `chat_json`；`keywords` 词表见 [util/keyword_lexicon.py](util/keyword_lexicon.py)）。

### 网页抓取（反爬回退）

命令与参数见 **[docs/steps/01-acquire.md](docs/steps/01-acquire.md)**；Playwright、微信 `#js_content` → MD 的细节见 **[util/README.md](util/README.md)**。Cursor 协作约定：`.cursor/rules/web-crawl-playwright-fallback.mdc`。

## 🎯 内容规范

### 标题格式

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

### 首页列表设计规范

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

### 移动端与排版

- 样式集中在 `css/style.css`：**正文**用 `clamp` 保证手机端约 **16～17px**、行高约 **1.8**；系统字体栈含 **PingFang / 微软雅黑**；`viewport-fit=cover` 与 **safe-area** 留白；词汇表外包裹 **`.vocab-table-wrap`** 以便窄屏横向滑动。
- 文章/列表的英文副标题用 **`<small class="title-en">`**，勿写死字号，随主标题缩放。

### 词汇标注规范

- 被识别的英文单词使用 `<span class="word-block">` 包裹，包含单词和音标释义
- **默认标单个英文词**；遇**报刊/行业固定搭配**时，可把整个搭配作为**一个**标注单位写入 `english-word`（允许空格或连字符，如 `on hold`、`dot plot`、`stop-loss`、`risk-free`），词汇表「词汇」列与正文**完全一致**。禁止的是把同一搭配**拆成两个紧挨的** `word-block`（见下「相邻 word-block」）。
- 优先标注**核心动词、形容词、关键名词**，跳过专有名词（如 Steve Jobs、Android 等）

#### 哪些词可以 / 不应被识别（选取原则）

1. **不识别（须严格执行）**：非常简单的日常高频词（如 yes、good、big、get、make、close、drop、go、see、take 等），**不因「混排出现」而破例**。
2. **不识别（须严格执行）**：中国普通高中英语课程标准范围内、无生僻义项的常见词（如 price、risk、trade、market、meeting、international、demand、flow、cancel、cost、gold、policy、chain、window、data、typical、emotion、giant、refuse、summit、domestic 等）。**宁可整段暂不标注，也不用上述词凑密度。**（若必须用英文承载「净额、净购」等义，优先改写句式或换用**机制词**如 `stockpile`、`gross`/`net` 结构上的替换词；避免单独为「常见义」标 `net` 凑数。）
3. **优先识别**：涉及文章**关键信息、因果、立场、数据判断**的词（英或汉均可；见下条「替换规则」），如 warning、closure、hawkish、sanctions、valuation、hedge、materialize 等。
4. **密度**：在**同一自然段内**，必须每 1 句 有**1 处** `word-block`。为避免与语文上的「复句/分句」混淆，**本文档中的「句」专指按下列标点切分后的片段**；**逗号 `，`、顿号 `、`、冒号 `：` 不断句**（除非你把它们改成句号等，或整段合并为一句后仍满足「每句一处」）。
5. **优先识别**：考研英语阅读中**常见、重要的动词与名词**，以及财经/科技语篇**学科用语**（如 token、ETF、GPU、architecture、monetization、hyperscale 等）。

**中文位置可译为英文替换（重要）**：当该中文在句中承载**观点、机制或数据判断**，且译成**单个英文单词**（或上条允许的**单一固定搭配**）后与原文义一致时，可将该位置**直接替换为该英文**，再对该片段加 `word-block`。专名、整句英译、一词多义易歧义处不要硬换。

**词汇表**须与正文中的 `word-block` **一一对应**（同一词形在文中多次出现仍只列一行），只收录正文中实际标注的词。

#### 落地标准（对标 `posts/2026-03-29-china-g7-europe-market.html`）

以下为该篇定稿时的**操作口径**，其他文章应与之对齐：

1. **句界与密度**：以 **`。` `？` `！` `；`** 为主划分「句」（仅在 **HTML 标签外**切分；`word-info` 释义里的 `；` 不参与断句）。**英文导语**里 ASCII **分号 `;`** 可视作分句。**同一自然段**默认指 **`<article class="post-content">` 内单个 `<p>...</p>`**（含仅含 `<strong>` 的短标题行也算一段）。**同一 `<p>` 内，每个按上述规则切出的「句」都必须含至少 1 处** `word-block`。若连续两句都没有可标的英文，则对其中一句做**中文 → 单个合规英文词**替换（见上条），**不得**用第 1～2 类「不识别」词凑数。**注意**：本条「句」与 `word-block` 密度**仅约束** `<article class="post-content">` 内部；置于 `</article>` 之后、词汇表之前的**来源与版权说明块**（见后文「外源素材与版权声明」）**不适用**密度与词汇表对应，且其中**不要**加 `word-block`。**`mingox build` 默认不把句级密度当作硬门禁**（仅「相邻 word-block」会失败退出）；密度与同位释义以人工对照本条及 `docs/ANNOTATION.md` 为准，`mingox validate` 可输出启发式密度警告（不导致失败）。
2. **朗读与规范的差异**：口语朗读时，一个 `<p>` 里用大量 **逗号** 连接的小停顿，听起来像多句话，但**按本规范仍可能只算少数几个「句」**；反之，为满足密度把若干原用句号写成的短句改成逗号连接，**规范上句数变少、每句需标注数也随之变少**。若你希望「凡朗读停顿处都要有词」，须**单独约定**（例如以逗号也断句），并与自检脚本同步，本文默认**不**以逗号断句。
3. **替换词取向**：优先选用**考研书面语、国际新闻常见搭配、财经/科技机制词**（如 `forgo` `acquiescence` `leverage` `stagnation` `interdependence` `backlash` `ramp` 等），使语气与中英混排政经稿一致。
4. **供应链表述**：涉及「供应链/物流」时，优先用 **logistics** 等**学科/行业上位词**承载语义；**不要**单独把 **chain**（高中常见）做成 `word-block`。
5. **完稿检查**：① 篇末「重点词汇」表与 **`<article class="post-content">` 内**正文标注**词形一致**（外源版权块中的词不列入表）；② 表格须为合法 HTML：`</thead>` 后必须有 **`<tbody>`** 再写 `<tr>`，勿出现只有 `</tbody>` 而无开始标签的残缺表；③ 运行下文「相邻 word-block」自检，**零命中**；④ 若为外源综述稿，版权说明块已置于文后且其中**无** `word-block`。
6. **双范文对照**：政经外交类以 G7 篇为主；**财经市场、利率与贵金属**等题材可同时对标 `posts/2026-03-29-gold-price-analysis.html`，复用其「固定搭配整块标、避免中英同义叠说、按段落功能补词」等做法（详见下节「案例补强」）。

#### 「相邻 word-block」的严格定义（必读）

两个 `word-block` **视为相邻**，当且仅当：前一个 `word-block` 的结束标记 `</span></span>` 与后一个 `<span class="word-block"` 之间**只有空白**（空格、换行、制表符），**没有任何其他字符**（包括英文单词、中文、标点）。

- **违规**：`</span></span> <span class="word-block"`（中间只有空格/换行）
- **合规**：`</span></span>问题，系统自动<span class="word-block"`（中间有中文）
- **合规**：`capital <span class="word-block"`（前一个英文词未加标注，与标注块之间有空格——空格左侧是未标注的英文，不是第二个 word-block）

**同一英文短语拆成两个标注**（如 gold price、safe haven、short position）一律按「相邻」处理，只能保留其中一个 `word-block`，另一个词保持纯文本；若该搭配在业界习惯上**不可拆**（如 `dot plot`、`risk-free`），应**整段放进同一个** `word-block` 的 `english-word` 中，而不是拆成两个块。

#### 案例补强（对标 `posts/2026-03-29-gold-price-analysis.html`）

金价稿在对齐 G7 密度、相邻规则与词汇表的过程里，形成以下**可复用操作**，可与上节「落地标准」对照执行：

1. **避免「英文 + 中文」同义叠说**：中文已说清楚动作时（如「暂停降息」），不要再在同一位置塞入与中文高度同义的单个英文词（易变成 `pause` + 暂停）；宜改用**固定搭配整体**（如 `on hold`）并加**极短补足语**（如「、未继续降息」），保持主叙事仍是中文流畅句。
2. **按段落功能选词（财经叙事）**：导语可用 `headline`、`echo`；数据可用 `snapshot`、`tracked`；利率与持有成本用 `real`（实际利率）、`carry`；联储框架用 `decision`、`on hold`、`dot plot`；市场主线用 `narrative`、`Fed`；技术位与路径用 `breach`、`stop-loss`、`support`、`replicate`、`triple`；交易与仓位用 `trim`、`allocation`、`scale`、`sideline`、`unload`、`unwind`；行情节奏用 `choppy`、`pullback`、`correction`、`bounce`、`entry`；央行行为优先用 **`stockpile`** 等机制词，少用第2类「不识别」清单里的词硬凑。
3. **正文中的英文碎片要「收口」**：混排里若出现 `risk-free` 等英文片段，须纳入 `word-block` 并进词汇表，避免「半标注、半原文」不统一。

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

### 外源素材与版权声明（综述 / 改编稿）

适用于根据**第三方公开内容**（如微信公众号长文、媒体报道等）撰写**要点综述、双语改编或学习向笔记**，而非本站独立采访或一手事实稿。

1. **不要放在文首**：来源、著作权归属、转载规则、原文链接、风险提示等**法律与礼仪性文字**，统一放在 **`</article>` 之后**、**「📖 重点词汇」小标题之前**，与正文在结构上分离；样式上应**醒目**（如边框、底色区分），便于读者一眼看到出处与权利边界。可参考 `posts/2026-04-01-private-fund-ai-hiring-threshold.html` 中的 `post-source-footer` 区块。
2. **该区块不加词汇标注**：版权说明区域内**不使用** `word-block`，其中出现的英文（如 URL）也不必拆成学习词条；篇末「重点词汇」表**只收录** `<article class="post-content">` 内实际标注的词，**不收录**仅为版权块而标的词。
3. **建议写清的事项**：第三方**平台与帐号名**、界面显示的**作者/署名**（若有）、**可点击的原文固定链接**；说明本站条目为**衍生整理**、不代为授权、不主张对原文的权利；商业转载与摘编由使用者自行联系**权利人**；并保留「不构成投资建议 / 法律意见」等**必要免责**（视题材酌定）。
4. **正文仍须合规**：`<article class="post-content">` 内仍完全遵守「词汇标注规范」与「落地标准」中的句界、`word-block` 密度、相邻块与词汇表一致性要求。
5. **抓取素材**：若简单 HTTP 拉取被风控（如微信「环境异常」），按「网页抓取（反爬回退）」与 `.cursor/rules/web-crawl-playwright-fallback.mdc` 在本机用 Playwright 等工具获取正文后再改编；**改编与抓取不等于取得转载授权**，发布与商用仍须遵守源站规则及著作权法。

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
        <div class="card">
            <article class="post-content">
                <h1>[emoji] 中文标题<br><small class="title-en">English Title</small></h1>
                <!-- 双语正文；词汇密度仅约束此 article 内 -->
            </article>
            <!-- 外源稿可选：来源与版权块（无 word-block），见「外源素材与版权声明」 -->
            <div class="subtitle">📖 重点词汇</div>
            <!-- 词汇表 ... -->
        </div>
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

## 🌐 部署到 EdgeOne Pages（静态 HTML）

本项目为**纯静态站点**（根目录 `index.html` + `posts/` + `css/` + `js/`），可用 [EdgeOne Pages](https://pages.edgeone.ai/) 官方 CLI 部署。更完整的代理说明见官方 Skill：[edgeone-pages-skills](https://github.com/edgeone-pages/edgeone-pages-skills)。

### 本仓库约定（新参与者按此对齐）

| 项 | 约定 |
|----|------|
| **EdgeOne 项目名** | 固定为 **`mingox`**（与远程已有项目同名时，CLI 会**复用该项目并上传新版本**，相当于覆盖线上内容） |
| **部署区域** | **中国站**使用 **`-a overseas`**（`pages deploy` 的 `area` 参数；勿与「国际站 `-a global`」混用） |
| **敏感信息** | API Token **仅放本地** `.edgeone/.token`（单行）；**勿提交**到 Git（已在 `.gitignore` 中忽略 `.edgeone/.token` 与 `.edgeone/*`） |

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

终端会打印 **`EDGEONE_DEPLOY_URL=...`**。

> ⚠️ **必须完整复制含 `?` 及之后全部查询参数的 URL** 访问预览！截断链接（去掉 `?eo_token=...` 部分）会导致页面无法打开或返回 404。
> 
> ✅ 正确：`https://mingox-xxx.edgeone.cool?eo_token=xxx&eo_time=xxx`
> ❌ 错误：`https://mingox-xxx.edgeone.cool`（缺少 token 参数）

可同时打开 CLI 给出的控制台部署详情链接排查构建与访问权限。

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

## 📄 许可证

MIT License
