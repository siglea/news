# 标注中间表示（IR）与流水线拆分 — 路线图（待评审）

**状态**：未实现。当前仓库仍为 **`mingox build` 单遍**：标注合并与 HTML 成稿同在 [workflow/build_draft.py](../../workflow/build_draft.py)。

本文档供评审「是否要做代码层解耦」时使用；**与 [docs/steps 索引](./README.md) 不冲突**——该索引已把概念上的第 2 / 3 步写清，当前实现仍是一条 `build`。

---

## 动机

- **概念**：第 2 步只维护与呈现无关的语义（段落、锚点 `zh`、`en`/`ipa`/`pos`/`gloss` 等）。  
- **第 3 步**：唯一负责映射为 `word-block`、词汇表 `<tbody>`、版权块，并跑相邻块等检查。  
- **现状耦合**：`apply_annotations_payload` / `annotate_paragraph` 直接产出带 `word-block` 的 `<p>`；`vocab_tbody_html` 从正文 HTML **反扫**提取词条。

---

## 建议技术方向

1. **定义 IR 文件**（示例名，待定）：如 `content/drafts/<slug>/03-body-annotations.json`，schema 含按段的标注列表（可与现有 chat/terms payload 对齐但**不含 HTML 字符串**）。
2. **拆分命令或子命令**（二选一或并存）：
   - `annotate`：MD + meta + 真源 → 写 IR + 可选人类可读任务 JSON；  
   - `render` / `build --html-only`：IR + meta → `posts/*.html`。  
   或保留单一 `build`，内部分两阶段但**强制落盘 IR** 便于 diff。
3. **渲染集中化**：「payload → 段落 HTML」单点实现；`vocab_tbody_html` 优先 **从 IR 生成**，HTML 反扫仅作一致性校验（可选）。
4. **校验分层**：相邻块在渲染后的段落 HTML 或最终 `posts` 上运行；密度启发式保持 WARN-only。
5. **回归**：多 slug `build` diff、`validate`、至少一篇 `keywords` 与一篇 `chat_json` 金样。

---

## 风险与前置工作

- Unicode 偏移、句切分与 HTML escape 边界。  
- 与现有 **`02-annotate-tasks.json`** 消费方（若有）的兼容与迁移策略。  
- 渲染器以 **`workflow/build_draft.py`** + **`util/annotate_lib.py`** 为单点；不再有独立 profile CLI。

评审通过后再开独立开发任务；**不要求**与文档四步目录一一对应新增四个 CLI。
