# MingoX 编辑与内容规范

**HTML/CSS 与成稿 DOM 契约**以 [docs/steps/03-html.md](./steps/03-html.md) 与实现代码为准。本文约定**标题、首页列表、摘要、词汇标注密度、相邻块、外源版权块**等编辑与版式规则。

**流水线**（取材 → 标注 → build → 发布）：[PIPELINE.md](./PIPELINE.md)。**标注引擎与机器校验**：[ANNOTATION.md](./ANNOTATION.md)。

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

- 样式集中在 `css/style.css`：**正文**用 `clamp` 保证手机端约 **16～17px**、行高约 **1.8**；系统字体栈含 **PingFang / 微软雅黑**；`viewport-fit=cover` 与 **safe-area** 留白；词汇表外包裹 **`.vocab-table-wrap`** 以便窄屏横向滑动。
- 文章/列表的英文副标题用 **`<small class="title-en">`**，勿写死字号，随主标题缩放。

## 词汇标注规范

- 被识别的英文单词使用 `<span class="word-block">` 包裹，包含单词和音标释义
- **默认标单个英文词**；遇**报刊/行业固定搭配**时，可把整个搭配作为**一个**标注单位写入 `english-word`（允许空格或连字符，如 `on hold`、`dot plot`、`stop-loss`、`risk-free`），词汇表「词汇」列与正文**完全一致**。禁止的是把同一搭配**拆成两个紧挨的** `word-block`（见下「相邻 word-block」）。
- 优先标注**核心动词、形容词、关键名词**，跳过专有名词（如 Steve Jobs、Android 等）
- **`chat_json` 义项与语域**：`en` / `gloss` 须与锚点中文**同义项、同语体**（中性职场/报道语境勿用苦役或文学大词顶替日常「工作」义；日常搭配如「全世界」勿用哲学/宇宙论专名硬套）。细则与反例见 [content/drafts/README.md](../content/drafts/README.md)「中英对齐范式」。
- **句义极性（必读）**：`en` 与 **`gloss` 所传达的褒贬、强弱**须与该句**整句语气**一致。反例：句意为「变化**最**明显」时，不得将锚点「明显」对成含「不明显、减弱」义的英文或释义（如 *muted* 类），造成**与原文相反**的阅读印象。完稿前对含「最、极、大幅、立竿见影」等强化语的句子做**快速扫检**。
- **机构 / 品牌与 `zh` 锚点**：`zh` 须为句内连续子串，但**避免**只截取会**在视觉上拆开机构全称**的片段，使读者误以为来源署名被拆碎（例：「钛媒体作者丨…」一句中，不宜只标「媒体」二字）。可改选同句内**不切开品牌**的子串（如「作者」），或换用该句中另一合法锚点。
- **朴实、通用的 `en`（与「考研书面语」并存）**：在义项准确的前提下，优先选用**国际新闻与职场英语里常见、读者易理解**的词形；避免仅为「显得高深」而选用极少见词、过度 literary 的隐喻或生硬 hyphen 拼接词。能用常见词说清时（如 *breakdown*、*wave*、*focus*、*wheel* 与语境一致），不必换成 *decomposition*、*zeitgeist*、*juggernaut* 等与句义不对等或过度炫学的表达。**全文 `en` 不得重复**时，应在**同义场里换常见词**，而非抬罕用词凑去重。

### 哪些词可以 / 不应被识别（选取原则）

1. **不识别（须严格执行）**：非常简单的日常高频词（如 yes、good、big、get、make、close、drop、go、see、take 等），**不因「混排出现」而破例**。
2. **不识别（须严格执行）**：中国普通高中英语课程标准范围内、无生僻义项的常见词（如 price、risk、trade、market、meeting、international、demand、flow、cancel、cost、gold、policy、chain、window、data、typical、emotion、giant、refuse、summit、domestic 等）。**不要用上述词单独凑密度。**在 **`chat_json` 路径**下，若句中无更优锚点，须改用**其它合规词**或**中文子串→合规英文**（见上「替换规则」），**不得**以「无词可标」为由对该句 `skip`（与 [ANNOTATION.md](./ANNOTATION.md) 默认引擎一致）。（若必须用英文承载「净额、净购」等义，优先改写句式或换用**机制词**如 `stockpile`、`gross`/`net` 结构上的替换词；避免单独为「常见义」标 `net` 凑数。）
3. **优先识别**：涉及文章**关键信息、因果、立场、数据判断**的词（英或汉均可；见下条「替换规则」），如 warning、closure、hawkish、sanctions、valuation、hedge、materialize 等。
4. **密度**：在**同一自然段内**，必须每 1 句 有**1 处** `word-block`。为避免与语文上的「复句/分句」混淆，**本文档中的「句」专指按下列标点切分后的片段**；**逗号 `，`、顿号 `、`、冒号 `：` 不断句**（除非你把它们改成句号等，或整段合并为一句后仍满足「每句一处」）。
5. **优先识别**：考研英语阅读中**常见、重要的动词与名词**，以及财经/科技语篇**学科用语**（如 token、ETF、GPU、architecture、monetization、hyperscale 等）。

**中文位置可译为英文替换（重要）**：当该中文在句中承载**观点、机制或数据判断**，且译成**单个英文单词**（或上条允许的**单一固定搭配**）后与原文义一致时，可将该位置**直接替换为该英文**，再对该片段加 `word-block`。专名、整句英译、一词多义易歧义处不要硬换。

**词汇表**须与正文中的 `word-block` **一一对应**（同一词形在文中多次出现仍只列一行），只收录正文中实际标注的词。

### `chat_json` 真源 vs 自动化工具（避免与「keywords 初稿」混淆）

- **成稿标准**：`annotate_engine=chat_json` 时，**`llm_annotations.json` 须由对话 LLM**（配合 `export-chat-bundle` 中的规则与上节选取原则）产出；**每一句（按 `annotate_merge` / `split_sentences` 与 export 对齐的序号）须有 1 处合格标注**，无故不得 `skip`；**全文 `en` 词形不得重复**（合并时 `annotate_merge.dedupe_in_order` 按顺序保留首次，后丢者须回到 JSON 里改词或换句锚点）。
- **`synth-lexicon-annotations`**：仅把全局词表 + 可选 `annotate_lexicon_extra` **子串匹配**到句上，**每句至多一词**、且与正文题材常不对口，**不得当作 chat_json 合格成稿**；它本质是 **keywords 思路的占位**，与上条「每句必标」冲突。
- **`workflow/gen_dense_chat_json.py`**：机器按词表子串匹配、**全文 en 去重**；**无匹配句 `skip`（保持原文）**，不生成占位词；**仍不替代** LLM 按义项精细选词。
- **`keywords` 引擎**：仅当编者在本篇 `meta.json` **显式**写出时使用；与 `chat_json` **二选一**，勿混为「先 synth 再当终稿」。

### 落地标准（对标 `posts/2026-03-29-china-g7-europe-market.html`）

以下为该篇定稿时的**操作口径**，其他文章应与之对齐：

1. **句界与密度**：以 **`。` `？` `！` `；`** 为主划分「句」（仅在 **HTML 标签外**切分；`word-info` 释义里的 `；` 不参与断句）。**英文导语**里 ASCII **分号 `;`** 可视作分句。**同一自然段**默认指 **`<article class="post-content">` 内单个 `<p>...</p>`**（含仅含 `<strong>` 的短标题行也算一段）。**同一 `<p>` 内，每个按上述规则切出的「句」都必须含至少 1 处** `word-block`。若连续两句都没有可标的英文，则对其中一句做**中文 → 单个合规英文词**替换（见上条），**不得**用第 1～2 类「不识别」词凑数。**注意**：本条「句」与 `word-block` 密度**仅约束** `<article class="post-content">` 内部；置于 `</article>` 之后、词汇表之前的**来源与版权说明块**（见后文「外源素材与版权声明」）**不适用**密度与词汇表对应，且其中**不要**加 `word-block`。**`mingox build` 默认不把句级密度当作硬门禁**（仅「相邻 word-block」会失败退出）；密度与同位释义以人工对照本条及 [ANNOTATION.md](./ANNOTATION.md) 为准，`mingox validate` 可输出启发式密度警告（不导致失败）。
2. **朗读与规范的差异**：口语朗读时，一个 `<p>` 里用大量 **逗号** 连接的小停顿，听起来像多句话，但**按本规范仍可能只算少数几个「句」**；反之，为满足密度把若干原用句号写成的短句改成逗号连接，**规范上句数变少、每句需标注数也随之变少**。若你希望「凡朗读停顿处都要有词」，须**单独约定**（例如以逗号也断句），并与自检脚本同步，本文默认**不**以逗号断句。
3. **替换词取向**：优先选用**考研书面语、国际新闻常见搭配、财经/科技机制词**（如 `forgo` `acquiescence` `leverage` `stagnation` `interdependence` `backlash` `ramp` 等），使语气与中英混排政经稿一致。
4. **供应链表述**：涉及「供应链/物流」时，优先用 **logistics** 等**学科/行业上位词**承载语义；**不要**单独把 **chain**（高中常见）做成 `word-block`。
5. **完稿检查**：① 篇末「重点词汇」表与 **`<article class="post-content">` 内**正文标注**词形一致**（外源版权块中的词不列入表）；② 表格须为合法 HTML：`</thead>` 后必须有 **`<tbody>`** 再写 `<tr>`，勿出现只有 `</tbody>` 而无开始标签的残缺表；③ 运行下文「相邻 word-block」自检，**零命中**；④ 若为外源综述稿，版权说明块已置于文后且其中**无** `word-block`。
6. **双范文对照**：政经外交类以 G7 篇为主；**财经市场、利率与贵金属**等题材可同时对标 `posts/2026-03-29-gold-price-analysis.html`，复用其「固定搭配整块标、避免中英同义叠说、按段落功能补词」等做法（详见下节「案例补强」）。

### 「相邻 word-block」的严格定义（必读）

两个 `word-block` **视为相邻**，当且仅当：前一个 `word-block` 的结束标记 `</span></span>` 与后一个 `<span class="word-block"` 之间**只有空白**（空格、换行、制表符），**没有任何其他字符**（包括英文单词、中文、标点）。

- **违规**：`</span></span> <span class="word-block"`（中间只有空格/换行）
- **合规**：`</span></span>问题，系统自动<span class="word-block"`（中间有中文）
- **合规**：`capital <span class="word-block"`（前一个英文词未加标注，与标注块之间有空格——空格左侧是未标注的英文，不是第二个 word-block）

**同一英文短语拆成两个标注**（如 gold price、safe haven、short position）一律按「相邻」处理，只能保留其中一个 `word-block`，另一个词保持纯文本；若该搭配在业界习惯上**不可拆**（如 `dot plot`、`risk-free`），应**整段放进同一个** `word-block` 的 `english-word` 中，而不是拆成两个块。

### 案例补强（对标 `posts/2026-03-29-gold-price-analysis.html`）

金价稿在对齐 G7 密度、相邻规则与词汇表的过程里，形成以下**可复用操作**，可与上节「落地标准」对照执行：

1. **避免「英文 + 中文」同义叠说**：中文已说清楚动作时（如「暂停降息」），不要再在同一位置塞入与中文高度同义的单个英文词（易变成 `pause` + 暂停）；宜改用**固定搭配整体**（如 `on hold`）并加**极短补足语**（如「、未继续降息」），保持主叙事仍是中文流畅句。
2. **按段落功能选词（财经叙事）**：导语可用 `headline`、`echo`；数据可用 `snapshot`、`tracked`；利率与持有成本用 `real`（实际利率）、`carry`；联储框架用 `decision`、`on hold`、`dot plot`；市场主线用 `narrative`、`Fed`；技术位与路径用 `breach`、`stop-loss`、`support`、`replicate`、`triple`；交易与仓位用 `trim`、`allocation`、`scale`、`sideline`、`unload`、`unwind`；行情节奏用 `choppy`、`pullback`、`correction`、`bounce`、`entry`；央行行为优先用 **`stockpile`** 等机制词，少用第2类「不识别」清单里的词硬凑。
3. **正文中的英文碎片要「收口」**：混排里若出现 `risk-free` 等英文片段，须纳入 `word-block` 并进词汇表，避免「半标注、半原文」不统一。

### 提交前自检（命令）

在仓库根目录执行，**无匹配输出**表示未发现相邻 `word-block`：

```bash
# 已安装 ripgrep 时
rg '</span></span>\s+<span class="word-block"' posts/

# 或仅用 grep
grep -rE '</span></span>[[:space:]]+<span class="word-block"' posts/*.html
```

若命中行，必须修改正文后再提交。可将此命令写入 CI 或本地 git hook。

### 连续标注示例（错误）

```html
<!-- 错误：capital 和 market 紧挨着，解释会重叠 -->
<span class="word-block"><span class="english-word">capital</span>...</span>
<span class="word-block"><span class="english-word">market</span>...</span>

<!-- 错误：stock 和 price 之间没有间隔 -->
<span class="word-block"><span class="english-word">stock</span>...</span>
<span class="word-block"><span class="english-word">price</span>...</span>
```

### 正确示例

```html
<!-- 正确：只标注最核心的单词 market -->
<span class="word-block"><span class="english-word">market</span><span class="word-info">[ˈmɑːkɪt] n. 市场</span></span>

<!-- 正确：surged 和 evaporated 之间有其他内容隔开 -->
<span class="word-block"><span class="english-word">surged</span><span class="word-info">[sɜːdʒd] v. 激增</span></span>近50倍...累计
<span class="word-block"><span class="english-word">evaporated</span><span class="word-info">[ɪˈvæpəreɪtɪd] v. 蒸发</span></span>超过...
```

### 技术实现约束

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

### 词汇表格式

词汇表必须包含**音标列**，表头格式：

```html
<thead>
    <tr><th>词汇</th><th>音标</th><th>词性</th><th>释义</th></tr>
</thead>
```

## 外源素材与版权声明（综述 / 改编稿）

适用于根据**第三方公开内容**（如微信公众号长文、媒体报道等）撰写**要点综述、双语改编或学习向笔记**，而非本站独立采访或一手事实稿。

1. **长版权块仍在文后；文首仅可有一句「出处提示」**：来源、著作权归属、转载规则、原文链接、风险提示等**法律与礼仪性长文**，统一放在 **`</article>` 之后**、**「📖 重点词汇」小标题之前**，与正文在结构上分离；样式上应**醒目**（如边框、底色区分），便于读者一眼看到出处与权利边界。可参考 `posts/2026-04-01-private-fund-ai-hiring-threshold.html` 中的 `post-source-footer` 区块。**经验**：部分读者只扫标题与首段，容易误以为「正文里看不到转载说明」；因此当 `meta.json` 中 **`include_source_footer` 为真**且填写了 **`source_account`** 时，`workflow/build_draft.py` → `util/annotate_lib.build_post_html` 会在 **`<h1>` 与首段 `<p>` 之间**自动插入 **`post-source-banner`**（一句，类名 `post-source-banner`），写明微信公众号名并**指向文末「来源与版权」**。**该横幅不是版权块的替代**，详细权利说明仍以文末 `post-source-footer` 为准。
2. **该区块不加词汇标注**：版权说明区域内**不使用** `word-block`，其中出现的英文（如 URL）也不必拆成学习词条；篇末「重点词汇」表**只收录** `<article class="post-content">` 内实际标注的词，**不收录**仅为版权块而标的词。
3. **建议写清的事项**：第三方**平台与帐号名**、界面显示的**作者/署名**（若有）、**可点击的原文固定链接**；说明本站条目为**衍生整理**、不代为授权、不主张对原文的权利；商业转载与摘编由使用者自行联系**权利人**；并保留「不构成投资建议 / 法律意见」等**必要免责**（视题材酌定）。
4. **正文仍须合规**：`<article class="post-content">` 内仍完全遵守「词汇标注规范」与「落地标准」中的句界、`word-block` 密度、相邻块与词汇表一致性要求。
5. **抓取素材**：若简单 HTTP 拉取被风控（如微信「环境异常」），按 [steps/01-acquire.md](./steps/01-acquire.md)、[util/README.md](../util/README.md) 在本机用 Playwright 等工具获取正文后再改编；若使用 Cursor，可额外参考仓库内 `.cursor/rules/web-crawl-playwright-fallback.mdc`（**非运行依赖**）。**改编与抓取不等于取得转载授权**，发布与商用仍须遵守源站规则及著作权法。

## 新稿与首页入口

**推荐路径**：使用 `python3 workflow/mingox.py init` → `acquire` → 标注 → `build` 生成 `posts/*.html` 并维护 `index.html` 列表，详见 [PIPELINE.md](./PIPELINE.md)。

以下为**手工编写或核对 HTML** 时的结构参考：

1. 在 `posts/` 目录创建新 HTML 文件，命名格式：**`YYYY-MM-DD-<题材 kebab>.html`**。`<题材 kebab>` 为**英文小写、连字符**的可读 slug（人名、机构、主题），须与正文题材一致，例如 `dai-yusen-tencent-ai-water-boiling`、`pinduoduo-xinpinmu-supply-chain`。**不要**用草稿目录名、流水线占位或 `wechat-<文章 id>` 当文件名；`meta.json` 里的 `slug`（草稿文件夹名）与 `out_html`（公开 URL 路径）可以不同。

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

3. 在 `index.html` 的内容列表中添加新链接（格式见上文「首页列表设计规范」）。

4. 提交并推送：

```bash
git add .
git commit -m "添加新内容：标题"
git push
```
