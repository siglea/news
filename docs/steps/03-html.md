# 第 3 步：HTML 成稿

本步对应：**由 `mingox build` 写出 `posts/*.html`**（含 `<article class="post-content">`、篇末词汇表占位、可选外源版权块），以及 **成稿后的校验**。

**实现入口**：[workflow/build_draft.py](../../workflow/build_draft.py) + [util/annotate_lib.py](../../util/annotate_lib.py)（`build_post_html`、`vocab_tbody_html` 等）。

**成稿文件名**：由 `meta.json` 的 **`out_html`** 决定，须为 **`posts/YYYY-MM-DD-<题材英文 kebab>.html`**；`<题材英文 kebab>` **必须以文章标题**（`title_zh` / `title_en`）为依据凝练，**勿**用 `wechat-<id>`、`mp-` 随机串等与标题脱节的占位。细则见 [content/drafts/README.md](../../content/drafts/README.md)「命名规范」与 [EDITORIAL.md](../EDITORIAL.md)「新稿与首页入口」。

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

- **正文容器**：`<article class="post-content">` 内为标题 `h1`（含 `<small class="title-en">`）、可选 **`post-source-banner` 出处一句**（`include_source_footer` + `source_account` 时由 `build_post_html` 注入，详见 [EDITORIAL.md](../EDITORIAL.md)「外源素材与版权声明」），以及多个 `<p>...</p>`。
- **词汇标注 DOM**（历史成稿或手工 HTML；样式见 [css/style.css](../../css/style.css)）：
  - `<span class="word-block">` → 内层 `<span class="english-word">` + `<span class="word-info">`（音标与释义）。
- **篇末词汇表**：`build_post_html` 生成表格；由 `vocab_tbody_html` 从正文 HTML **反扫** `word-block`（`build` 已强制要求 `llm_annotations.json`，正常成稿 tbody 由标注决定）。
- **外源版权**：`meta.json` 中 `include_source_footer`、`footer_template`（`verbatim` / `derivative`）、`footer_derivative_mp_unknown`、`source_author_display`、`risk_blurb_secondary` 等；条文见 [EDITORIAL.md](../EDITORIAL.md)。

---

## 机器校验（与语义规范的分工）

| 类型 | 位置 | 说明 |
|------|------|------|
| 相邻 `word-block` | `build` 默认 + `mingox validate` | **硬门禁**（若生成 HTML 中含 `word-block`），失败 exit 1 |
| 句级密度 | `validate` | **仅 WARN**，启发式；针对含 `word-block` 的正文 |

**`mingox build` 默认不校验句级密度**。

---

## 规范索引（编辑规范全文）

以下内容的**完整条文**在 **[EDITORIAL.md](../EDITORIAL.md)**，本篇不重复拷贝：

- 首页列表、标题格式、标签、摘要、外源素材与版权声明  
- 历史成稿中 `word-block` 与词汇表相关约定（若手工维护 HTML）  

**标注步骤**：[02-annotate.md](./02-annotate.md)、[content/drafts/README.md](../../content/drafts/README.md)。

---

## 下一步

- 发布：**[04-publish.md](./04-publish.md)**
