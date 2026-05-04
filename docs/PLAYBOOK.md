# MX 协作与发稿 Playbook（v1）

目标：在不牺牲质量的前提下，减少返工与重复 deploy，把稳定吞吐拉到可预期区间。

适用：`mx` 新稿全流程（URL -> 草稿 -> 标注 -> 成稿 -> 首页 -> 发布）。

与 `docs/TOOLING.md` 关系：本 Playbook 将复盘经验转成可执行清单。**协作、审发节奏、deploy 约定**以 **本文** 为准；**命令、路径与工具事实**以 **TOOLING** 为准。

---

## 0) 开工前分工（防重复）

- 在 thread 先发 `claim + 范围 + 输出物 + 角色（执行/审核）`，确认不重叠后再开工。
- 推荐并行模式：
  - **执行位**：跑稿件主链路（init/acquire/annotate/build/validate）。
  - **审核位**：做 dry-run 复核（正文尾巴、索引、首页、发布前检查）。
- 看到对方 claim 为**执行位**后，严禁本地并行跑同一篇主链路；仅执行方可跑完整流程。
- 看到对方 claim 为**审核位**后，等待执行方 push/回帖，再介入 review 与 QA。
- 合并前必须互相 check；范围冲突时先在 thread 改派。
- claim 示例：
  - `@claude claim: 角色=执行 | 范围=workflow/X.py(+test) | 输出=PR-N | 不动 docs/`
  - `@cursor claim: 角色=审核 | 范围=li-auto 稿件 QA | 输出=review 回帖`

---

## 1) 标准发布节奏（先审后发）

1. `init -> acquire -> export-chat-bundle -> 标注 -> close-loop(不带 deploy)`
2. 审核位按“发布前必查清单”通过后，再执行一次 `deploy`
3. 发布后做线上抽检（200/404）

关键规则：**默认单次 deploy**。除非必须修复线上问题，否则不重复部署。

---

## 2) 发布前必查清单（必须执行）

### A. 源内容清理
- `01-source.md` 末尾不得包含运营文案（如“扫描二维码/添加小助手/关注公众号/阅读原文/长按识别”）。
- 允许保留有信息价值的原文来源链接（如播客/视频原链接）。
- 自动化检查：`python3 workflow/mingox.py normalize-source --slug <slug> --check`（发现高置信尾巴时 exit 1，可作为 `close-loop` 前置 gate）。

### B. 标注一致性
- `validate --annotations --slug <slug>` 必须通过（无 FAIL）。
- `llm_annotations.json` 的索引范围必须与句数一致（无越界 `i`）。
- 长稿建议目标：non-skip `>= 90%`（最低门槛仍为 80%）。

### C. 首页入口
- `index.html` 顶部 `<li>` 已更新，标题/摘要/标签格式符合规范。
- 新稿链接与 `meta.json.out_html` 完全一致。

### D. 命名与元数据
- `meta.json.title_zh` 使用标准字符（禁用兼容/部首替代字），且不追加来源后缀（如 `｜甲子光年`）。
- `meta.json.tags` 为必填（建议 7-10 项，含主题词 + 来源标签如 `转载`）；禁止依赖默认回退为单 `转载`。
- `meta.json.title_zh`、`index.html` 对应 `<li>`、`posts/*.html` 的 `<title>/<h1>` 必须三处一致。
- **`article_layout`（正文 DOM）**：**默认不写或 `flat`/`classic`** → 与历史稿一致的扁平 `<p>` + `<figure>`。**适用微信长篇、需要卡片化分段视觉时** 可设 **`segments`**（或仅用 CLI `--segments` 试 build）。**一旦启用/关闭 segments 或改过启发式相关源码，必须重跑 `export-chat-bundle` 并重做标注**，禁止在句表已变的情况下沿用旧 `llm_annotations.json`。需要对照扁平 DOM 时用 **`--no-segments`**。详见 [steps/03-html.md](./steps/03-html.md)。

---

## 3) 发布后抽检（必须执行）

- 成稿页 200：`/posts/<date>-<slug>.html`
- 内部资源 404：
  - `/util/annotate_lib.py`
  - `/content/drafts/<slug>/01-source.md`

若 404 抽检失败，视为发布质量问题，立即回滚到修复流程。
回滚定义：修源文件 -> 重跑 `close-loop --deploy`（EdgeOne 以最新 deployment 覆盖线上）；通常不需要 `git revert`。

---

## 4) 耗时基线（当前实测）

基于近期实测样本（长稿）：

- `annotations-gate/build/validate`：毫秒级（< 1s）
- `deploy`：约 40s（当前 close-loop 最大项）
- 长稿标注：分钟级（当前端到端最大项）

策略含义：
- 短链路优化重点：减少重复 deploy。
- 长链路优化重点：提升标注阶段稳定性与返工控制。

---

## 5) 异常处理约定

- 若清理正文导致句数变化，必须同步校验并修正 annotations 索引后再 build。
- 若 deploy 后发现 must-fix：
  1. 修复源文件（优先 `01-source.md`）
  2. 重跑 `close-loop` 与 `deploy`
  3. 回帖说明修复点、Deployment ID、新预览链接

---

## 6) Thread 回帖模板（执行位）

- 本次 URL：
- slug / out_html：
- 标注结果（non-skip）：
- 标注方式（subagent / 主代理直跑）：
- `close-loop` 结果：
- Deployment ID：
- 预览 URL（完整 eo_token 参数）：
- 抽检结果（post=200, util=404, drafts=404）：
- profile（可选，`MX_PROFILE=1`）：

