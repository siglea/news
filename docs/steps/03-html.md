# 第 3 步：HTML 成稿

本步对应：**由 `mingox build` 写出 `posts/*.html`**（含 `<article class="post-content">`、词汇表、可选外源版权块），以及 **成稿后的校验**。

**实现入口**：[workflow/build_draft.py](../../workflow/build_draft.py) + [util/annotate_lib.py](../../util/annotate_lib.py)（`build_post_html`、`vocab_tbody_html` 等）。

---

## 命令

```bash
python3 workflow/mingox.py build --slug my-topic
# 调试可跳过相邻检测:
python3 workflow/mingox.py build --slug my-topic --skip-validate
python3 workflow/mingox.py validate
python3 workflow/mingox.py validate --post posts/2026-03-29-china-g7-europe-market.html
```

---

## 页面结构约定

- **正文容器**：`<article class="post-content">` 内为标题 `h1`（含 `<small class="title-en">`）与多个 `<p>...</p>`。
- **词汇标注 DOM**（样式由 [css/style.css](../../css/style.css) 消费）：
  - `<span class="word-block">` → 内层 `<span class="english-word">` + `<span class="word-info">`（音标与释义）。
- **篇末词汇表**：`build_post_html` 生成表格；**当前实现**从正文 HTML **反扫** `word-block` 汇总行（非单独 IR 文件）。
- **外源版权**：`meta.json` 中 `include_source_footer`、`footer_template`（`verbatim` / `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary` 等；条文见根 [README.md](../../README.md)「外源素材与版权声明」等章节。

---

## 机器校验（与语义规范的分工）

| 类型 | 位置 | 说明 |
|------|------|------|
| 相邻 `word-block` | `build` 默认 + `mingox validate` | **硬门禁**，失败 exit 1 |
| 句级密度 | `validate` | **仅 WARN**，启发式；见 [docs/ANNOTATION.md](../ANNOTATION.md) |

**`mingox build` 默认不校验句级密度**；密度、同位释义以根 **README** + 人工为准（README「落地标准」条）。

---

## 规范索引（仍以根 README 为全文权威）

以下内容的**完整条文**在根目录 **[README.md](../../README.md)**，本篇不重复拷贝：

- 词汇选取、句界与密度、落地标准、相邻 `word-block` 定义、案例补强  
- 首页列表、标题格式、标签、摘要、外源素材与版权声明  
- `word-block` / 词汇表 HTML 合法性与自检清单  

**标注语义与词表文件**：[02-annotate.md](./02-annotate.md)、[content/drafts/README.md](../../content/drafts/README.md)。

---

## 微信 profile 捷径（不经 MD 草稿）

已抓取 `util/.crawl-output/...-js_content.html` 时，配置 `util/article-profiles.json` 后：

```bash
python3 workflow/mingox.py wechat --profile your-profile-key
```

与主路径共用 **`build_post_html`** 的 HTML 契约。

---

## 下一步

**[04-publish.md](./04-publish.md)**：`serve` / `deploy` / Gitee。
