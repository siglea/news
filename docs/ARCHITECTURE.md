# 标注中间表示（IR）与流水线拆分 — 路线图（待评审）

**位置**：本文件为 `docs/ARCHITECTURE.md`，与 [TOOLING.md](./TOOLING.md)、[PLAYBOOK.md](./PLAYBOOK.md)、[steps/README.md](./steps/README.md) 同级；描述**未来可选**的代码层拆分，不是当前必读的发稿步骤。

**状态**：未实现。当前 **`mingox build`** 仍为单遍：`annotate_merge` 合并 `llm_annotations.json` → `build_post_html`；**无**独立 IR 真源文件。

本文档供评审「未来是否引入独立标注层」时使用；与 [docs/steps 索引](./steps/README.md) 中第 2 步说明对照阅读。

---

## 动机（未来）

- **概念**：第 2 步只维护与呈现无关的语义（段落、锚点、词条字段等）。  
- **第 3 步**：映射为 `word-block`、词汇表 `<tbody>`、版权块，并跑相邻块等检查。  
- **现状**：`annotate_merge` + `llm_annotations.json` 为当前标注路径；`vocab_tbody_html` 可从成稿 HTML **反扫** `word-block`。

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
