# 草稿目录 `content/drafts/<slug>/`

每篇待发布内容一个子目录（`slug` 用小写、连字符）。

## 文件一览

| 文件 | 说明 |
|------|------|
| `meta.json` | 标题、英文题、`out_html`、来源 URL、`include_source_footer`、`footer_template`（`verbatim` \| `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary`、**`annotate_engine`**（见下）等。可用 `python3 workflow/mingox.py init ...` 生成模板。 |
| `out_html` 命名 | **`posts/YYYY-MM-DD-<题材>.html`**：`<题材>` 为**可读英文 kebab**（人名、公司、主题词），与范文 `posts/2026-04-03-pinduoduo-xinpinmu-supply-chain.html` 一致。**禁止**用草稿目录名或微信文章 id 当文件名（如 `wechat-ymssqxei`）；`init` 的 `--slug` 可与 `out_html` 不同。改路径后需同步 `index.html` 与站内链接。 |
| `01-source.md` | **第 1 步**输出的正文（Markdown，按空行分段）。微信 HTML 以 section/leaf 为主时，由 `annotate_lib` 的 **plain/leaf 回退抽取**生成；偶见首段符号（如 `▎`）可手删后重建。 |
| `02-annotate-tasks.json` | **第 2 步**由 `mingox build` 生成的复合任务快照（可复查、可版本管理）。 |
| **`llm_annotations.json`** | 当 `annotate_engine` 为 **`chat_json`** 时，须按 `export-chat-bundle` 规则由**大模型对话或等价方式**产出（**每句至少 1 处、全文 `en` 不重复**，见 [EDITORIAL.md](../../docs/EDITORIAL.md)「chat_json 真源 vs 自动化工具」）。**不依赖 Cursor**：任意 LLM 界面或手改 JSON 均可，只要满足 [docs/ANNOTATION.md](../../docs/ANNOTATION.md)「非 Cursor 环境」一节。**`synth-lexicon-annotations` 仅为 keywords 式稀疏占位，不得当终稿。** 应急可 `gen_dense_chat_json.py`（最长 `zh` 优先）或 **`gen_shortest_zh_chat_json.py`**（最短 `zh` 优先）；无命中句可能为 `skip`，须对话补全。 |
| `annotate_lexicon_extra.json` | （可选）**仅编者明示**时添加；由 `gen_dense_chat_json.py` / `synth-lexicon-annotations` 等合并进候选词表。**不得**为抬高机器命中率擅自新建；**不替代**对话终稿。 |
| `llm-chat-bundle.json` | （可选）`export-chat-bundle` 导出，供把 `system_prompt` + `sentences` 交给大模型（任意客户端）后写回 `llm_annotations.json`。 |

抓取缓存仍在 **`util/.crawl-output/`**（不提交），此处只放编辑定稿与元数据。微信抓取技巧与段落抽取逻辑见 **[util/README.md](../../util/README.md)**。

---

## 标注引擎（`meta.json`）

**仓库约定**：**默认 `chat_json`**；**只有编者单独说明「本篇用 keywords」等时**才改 `annotate_engine`。不要用 `keywords` 替代对话标注，除非明确要求（否则词汇密度往往远低于 [EDITORIAL.md](../../docs/EDITORIAL.md)）。

| `annotate_engine` | 行为 |
|-------------------|------|
| **`chat_json`**（**默认推荐新稿**） | 读 **`llm_annotations_file`**（默认 `llm_annotations.json`），经 `util/annotate_merge.py` 校验、去重后渲染。先 `python3 workflow/mingox.py export-chat-bundle --slug <slug>` 再对话产出 JSON。 |
| **`keywords`**（非默认；**须 `meta` 显式写出**，且仅编者单独要求时使用） | 使用仓库全局词表 [util/keyword_lexicon.py](../../util/keyword_lexicon.py)（经 `annotate_lib` 暴露为 **`KEYWORDS`**）做子串匹配；`keyword_dedupe: false` 可关闭全文按英文词形去重。 |

**标注环节总览**（引擎决策树、真源禁区、`validate` 能力边界）：**[docs/ANNOTATION.md](../../docs/ANNOTATION.md)**。**第 2 步分册**：[docs/steps/02-annotate.md](../../docs/steps/02-annotate.md)。四步索引见 **[docs/steps/README.md](../../docs/steps/README.md)**、[PIPELINE.md](../../docs/PIPELINE.md)。

---

## 推荐工作流（从 `01-source.md` 出发，**`chat_json` 主路径**）

1. **`python3 workflow/mingox.py export-chat-bundle --slug <slug>`**，将 bundle 中的 `system_prompt` 与 `sentences` 交给**任意大模型或助手**（网页、API、IDE 插件等，**不必 Cursor**），产出 **`{"version":1,"annotations":[...]}`**，保存为 **`llm_annotations.json`**（**每句须有标、勿无故 skip；全文 `en` 不重复**）。**不要**用 `synth-lexicon-annotations` 代替本条。仅应急时可 **`python3 workflow/gen_dense_chat_json.py <slug>`** 或 **`python3 workflow/gen_shortest_zh_chat_json.py <slug>`** 铺词表命中，无匹配句保持原文（`skip`），再补全。  
2. **`meta.json`** 设 **`"annotate_engine": "chat_json"`**（及可选的 `llm_annotations_file`）。  
3. **`python3 workflow/mingox.py build --slug <slug>`** → 生成 `02-annotate-tasks.json` 与 `posts/*.html`。  
4. 若合并 stderr 提示缺句/校验失败，**改 JSON 或再跑一轮大模型**补全；成稿后仍按 [docs/EDITORIAL.md](../../docs/EDITORIAL.md) 做密度与相邻块人工扫。  

---

## 中英对齐范式（对义项锚定）

**原则**：`en` 必须是读者看到这段 **`zh`** 时，**最直接对应的英文词/复合词**（同位释义），用于词汇表「中文—英文」对齐。

**避免**：

- 用**同句或同话题里相关但不同位**的词顶替，例如：「学习轨迹」对 **trajectory / path**，不要对 **analytics**；「数字员工」对岗位/分身类概念，不要对 **staffing**（编制配置）；「财务业绩」在财报语境对 **earnings** 等，不要仅用泛称 **results**；「品牌出海」对 **outbound** 等外向扩张义，不要仅用泛称 **globalization**；「龙头壁垒」若正文无「护城河」比喻，优先 **barrier** 等与「壁垒」字面/商业义对齐的词，避免强行 **moat**。
- **`gloss` 写成中文片段的复述**却不解释 **`en`**（如用「联合领投」解释 *syndicate* 而不用「银团」类义项）。
- **语体与语域错位**：中文是中性职场/报道语体时，英文勿选带明显贬义、文学古雅或「苦役」色彩的词（如「在航天行业工作多年」应对 **work** 一类任职义，不宜用 *toil*「苦活」）。
- **大词硬套日常搭配**：中文是常见搭配（如「全世界的科学家」）时，勿用哲学/宇宙论专名（如 *macrocosm*「宏观宇宙/大千世界」）顶替；宜对 **worldwide / global / around the world** 等与「全球范围」义对齐的词，并在 `gloss` 中体现「遍及世界」而非玄学色彩。
- **句义弄反**：`gloss` 须与**该句**语气一致；含「最明显、大幅提升」等强化表述时，英文义项不得写成削弱或反义（如「明显」勿对成「不明显」）。
- **拆开机构名**：`zh` 虽须最短，但若会**切开**「钛媒体」等机构全称、造成署名像被拆碎，应改标「作者」等同句子串或换锚点（参见 [EDITORIAL.md](../../docs/EDITORIAL.md)「词汇标注规范」）。
- **为显学问而罕用词**：义项相同时优先**新闻/职场常见**英文；避免 *zeitgeist*、*juggernaut*、*decomposition* 等与句义不对等或读者难用的「大词」，除非原文风格即如此。

**`chat_json` / 对话产出**：须遵守 `export-chat-bundle` 内 **`system_prompt`**（含上述义项锚定与 `zh` 最短化等条）。若同时使用 **`underline`**，合并时会**折叠为最短 `zh`**（以 `underline` 为准）；新稿建议只写最短 **`zh`**，不填 `underline`。

---

## 词汇偏少（`keywords` 模式）

自动化仅标注全局词表 [util/keyword_lexicon.py](../../util/keyword_lexicon.py) 与正文**字面命中**的片段（宁缺毋滥）。若成稿「重点词汇」表过短，在 **`_KEYWORD_ENTRIES` 中增补该稿实际出现的术语**（长短语优先、英文词位无空格、可用连字符），再 `mingox build`。

**`meta.json`（微信 `url` 抓取后）**：**`title_zh` 会被更新为微信页标题**（覆盖 init 时的占位题）；`source_account` 等为抓取侧写入。英文题、`meta_description`、风险提示等常需 **人工补全** 后再 `build`。
