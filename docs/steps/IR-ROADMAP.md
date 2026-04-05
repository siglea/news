# 标注中间表示（IR）与流水线拆分 — 路线图（待评审）

**状态**：未实现。当前 **`mingox build`** 为单遍：Markdown 段落 → 转义 `<p>` → `build_post_html`；**无**独立标注真源文件。

本文档供评审「未来是否重新引入标注层」时使用；与 [docs/steps 索引](./README.md) 中第 2 步占位说明一致。

---

## 动机（未来）

- **概念**：第 2 步只维护与呈现无关的语义（段落、锚点、词条字段等）。  
- **第 3 步**：映射为 `word-block`、词汇表 `<tbody>`、版权块，并跑相邻块等检查。  
- **现状**：旧 `chat_json` / `annotate_merge` 已移除；`vocab_tbody_html` 仍可从正文 HTML **反扫** `word-block`（手工或未来生成器写入时）。

---

## 建议技术方向（草案）

1. **定义 IR 文件**（示例名，待定）：如 `content/drafts/<slug>/03-body-annotations.json`，schema 含按段的标注列表（**不含 HTML 字符串**）。
2. **拆分命令**（二选一或并存）：`annotate` → IR；`render` / `build --html-only` → `posts/*.html`。
3. **渲染集中化**：IR → 段落 HTML 单点实现；`vocab_tbody_html` 优先从 IR 生成（可选）。
4. **校验分层**：相邻块在渲染后的段落 HTML 或最终 `posts` 上运行；密度启发式保持 WARN-only。
5. **回归**：多 slug `build` diff、`validate`。

---

## 风险与前置工作

- Unicode 偏移、句切分与 HTML escape 边界。  
- 与现有 **`02-annotate-tasks.json`** 消费方（若有）的兼容与迁移策略。  
- 渲染器以 **`workflow/build_draft.py`** + **`util/annotate_lib.py`** 为扩展点。

评审通过后再开独立开发任务。
