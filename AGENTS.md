# AGENTS.md — MingoX

## 项目概览

MingoX 是多语言（中英混排）多媒体内容平台，通过四步流水线生产带词汇标注的静态 HTML 文章并发布。

- **主 CLI**：`python3 workflow/mingox.py <command>`
- **文档地图**：`docs/README.md` → `docs/TOOLING.md`（命令与路径权威）→ `docs/PLAYBOOK.md`（协作节奏）→ `docs/EDITORIAL.md`（编辑规范）
- **四步分册**：`docs/steps/01-acquire.md` → `02-annotate.md` → `03-html.md` → `04-publish.md`

## 环境与依赖

| 依赖 | 安装 |
|------|------|
| Python 3.10+ | `pip3 install -r workflow/requirements.txt` |
| Playwright（微信抓取） | `pip3 install -r util/requirements-crawl.txt && python3 -m playwright install chromium` |
| Node.js ≥ 16（部署） | `npx edgeone@latest` |

## 核心命令

### 新稿全流程（必须按顺序）

```bash
# 0. 预检（每次发稿前必跑）
git fetch && git status                              # 确保不落后 origin/master
git grep -l "<标题关键词>" content/drafts/ posts/    # 去重，防止题材重复

# 1. 初始化
python3 workflow/mingox.py init --slug <英文kebab> --out-html YYYY-MM-DD-<kebab> --title-emoji <emoji>

# 2. 抓取
python3 workflow/mingox.py acquire --slug <slug> --mode url --url "<URL>"

# 3. 导出标注 bundle
python3 workflow/mingox.py export-chat-bundle --slug <slug>

# 4. 标注（派 subagent 执行，主代理只调度与 review）
#    读取 content/drafts/<slug>/llm-chat-bundle.json，按 instructions 字段执行

# 5. 闭环（标注 gate → build → validate）
python3 workflow/mingox.py close-loop --slug <slug>

# 6. 手动更新 index.html 的 <ul class="post-list"> 添加新稿 <li>

# 7. 部署（多 agent 协作时先在 thread claim deploy）
python3 workflow/mingox.py deploy
```

### 快捷命令

```bash
make ci-scope              # 日常迭代：按 git diff 决定跑啥
make ci                    # 合并前全量：test + validate
make test                  # workflow/tests/test_*.py
make validate              # annotations + posts 质量门禁
make dist                  # 构建 ./dist 白名单目录
```

### 常用 CLI 子命令

| 命令 | 作用 |
|------|------|
| `mingox init` | 创建草稿目录 `content/drafts/<slug>/` |
| `mingox acquire` | URL/paste → `01-source.md` |
| `mingox export-chat-bundle` | 导出 `llm-chat-bundle.json` 供 LLM 标注 |
| `mingox build` | 合并标注 → `posts/*.html`（**无 `llm_annotations.json` 则失败**） |
| `mingox validate` | 相邻 word-block 检测 + 密度启发式 WARN |
| `mingox close-loop` | annotations-gate → build → validate（加 `--deploy` 含发布） |
| `mingox serve` | 本地预览 `--port 8765` |
| `mingox deploy` | EdgeOne Pages 部署 |

## 关键约束

### 标注
- **`llm_annotations.json` 是 build 的前置必填**，缺失则 build 失败
- `zh` 与 `en` 必须一一对应；non-skip ≥ 80%（长稿目标 ≥ 90%）
- **支持 subagent 的 harness 默认派子代理跑标注**，主代理不逐句消耗 token
- 若启用/关闭 `segments` 或改动正文句数，**必须重跑 `export-chat-bundle` 并重做标注**

### 命名
- **slug 与 `out_html` 必须以文章标题凝练英文 kebab**，禁止 `wechat-<id>` 等随机串
- `title_emoji` 按题材选：📈 新闻/财经、💡 思想/观点、📜 文化/诗词

### 部署
- **EdgeOne Token**：人维护在 `~/.edgeone/token`（chmod 600），agent deploy 前复制到 `<repo>/.edgeone/.token`
- **Gitee PAT**：人维护在 `~/.gitee`（chmod 600）
- **两者绝不进 git、绝不贴公开频道**
- **deploy 串行协议**：在 thread 发 `claim deploy` 后再执行，其他 agent 看到 claim 不并发
- 部署后必须回传**完整预览 URL（含 `?eo_token=...` 全部参数）**，裸域名会 401
- **部署后 404 抽检**：`/posts/<date>-<slug>.html` 应 200；`/util/...py`、`/content/drafts/...md` 应 404

### 发布 ≠ 部署成功
- **`index.html` 必须手动更新**，否则读者在首页看不到新稿
- 发布前必查：`01-source.md` 末尾无运营文案、`validate --annotations` 通过、首页 `<li>` 与 `meta.json.out_html` 一致

### Harness 中立
- 仓库不绑定任何 AI 编程工具；`.claude/`、`.cursor/`、`.aider*` 等已 gitignore
- 标注触发口令通过 `export-chat-bundle` 输出，任意对话式 LLM 客户端均可执行

## 目录职责速查

| 路径 | 职责 |
|------|------|
| `content/drafts/<slug>/` | 单篇草稿：`meta.json`、`01-source.md`、`llm_annotations.json` |
| `workflow/` | `mingox.py` CLI 入口 + 流水线模块 |
| `util/annotate_lib.py` | 微信抽取、`build_post_html`、词汇表反扫 |
| `util/annotate_merge.py` | 标注合并；system prompt 来自 `util/prompts/chat_annotate_system.txt` |
| `posts/` | 成稿静态 HTML |
| `tools/build_dist.sh` | 构建 `./dist` 白名单（不含 drafts/源码） |

## 验证链接须走到发布

当任务是验证某篇文章 URL 时，确认抓取可行后**默认继续完成整条主路径并执行发布**，不要停在「单独 crawl 成功」。

## 性能分析

需要测量步骤耗时：设 `MX_PROFILE=1` 环境变量，每步会在 stderr 输出 `dur_ms`。

## 未实现/路线图

- `docs/ARCHITECTURE.md` 描述的是**未来可选**的标注 IR 拆分方案，**当前未实现**，不要按此文档工作
