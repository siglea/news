# 入门：环境与第一篇 walkthrough

完成 [TOOLING.md](./TOOLING.md) 与 [steps/](./steps/README.md) 四步前，请在本机准备依赖；**协作节奏与 deploy 清单**见 [PLAYBOOK.md](./PLAYBOOK.md)。

## 第一篇 walkthrough（最小闭环）

1. 按下文安装 **Python** / **Playwright** / **workflow 依赖**；可选建 `.venv`，在仓库根执行 `make ci PYTHON=.venv/bin/python` 确认环境。
2. `python3 workflow/mingox.py init ...` 生成 `content/drafts/<slug>/`（参数与命名见 [content/drafts/README.md](../content/drafts/README.md)）。
3. `acquire` → `export-chat-bundle` → 产出 `llm_annotations.json` → `build` → `validate` 的命令与边界见 **[TOOLING.md](./TOOLING.md)** 与 **[steps/01-acquire.md](./steps/01-acquire.md)** 起的分步文档。
4. 发布前检查与 deploy 串行约定见 **[PLAYBOOK.md](./PLAYBOOK.md)**。

## Git

- 安装 Git，仓库克隆后用于版本管理与提交 `posts/`、`index.html` 等。

## Python

- 建议 **Python 3.10+**。
- 微信抓取（Playwright）：

```bash
pip3 install -r util/requirements-crawl.txt
python3 -m playwright install chromium
```

- 流水线第 1 步（普通网页 URL、DuckDuckGo 检索，可选）：

```bash
pip3 install -r workflow/requirements.txt
```

## Node.js 与 EdgeOne（第 4 步部署）

- **Node.js ≥ 16**、npm。
- 中国站部署见 [docs/steps/04-publish.md](./steps/04-publish.md)「EdgeOne Pages（CLI 细则）」：推荐 `npx edgeone@latest pages deploy -a overseas -n mingox`，Token 放 `.edgeone/.token`（勿提交）。一键入口：`python3 workflow/mingox.py deploy`。

## 小结

| 步骤 | 依赖 |
|------|------|
| 1 获取原文 | `workflow/requirements.txt`；微信域名另需 Playwright |
| 2 标注 | `export-chat-bundle` + 大模型产出 `llm_annotations.json`（见 steps/02-annotate.md）；**build 前必填** |
| 3 出 HTML | 同上 |
| 4 本地预览 | 仅 Python：`python -m http.server` |
| 4 远程发布 | Node + EdgeOne CLI |

## 本地 / CI 一键检查

仓库根有 **`Makefile`**，封装了常用检查命令。**日常迭代推荐 `make ci-scope`**（按 git diff 自动决定跑啥），**合并前推荐 `make ci`**（全量兜底）：

```bash
make ci-scope              # 按 git diff 决定跑啥（日常迭代推荐）
make ci                    # test + validate（合并前全量兜底）
make test                  # workflow/tests/test_*.py 单元测试
make validate-annotations  # 全部草稿的 llm_annotations.json 质量门禁
make validate-posts        # posts/*.html 版式校验
make validate              # annotations + posts
```

### `make ci-scope` 路由规则（见 [tools/ci_scope.sh](../tools/ci_scope.sh)）

| 改动路径 | 跑什么 |
|---------|--------|
| `util/*.py`、`workflow/*.py` | `make test` + `make validate` |
| `posts/*`、`index.html`、`tools/*`、`Makefile`、`edgeone.json`、`_config.yml` | `make validate` |
| `content/drafts/*` | `make validate` |
| 仅 `*.md` 或 `docs/*` | 跳过（仅文档无 CI 门禁；合并前请用 `make ci` 兜底） |
| 其它 | `make validate`（保守） |

`make ci-scope` 默认对比 `origin/master`；若想看已 staged 的改动，可直接 `bash tools/ci_scope.sh --staged`。

如果你已经建好 `.venv`，可显式覆盖 Python 二进制：

```bash
make ci PYTHON=.venv/bin/python
make ci-scope     # 内部 make 调用会继承 PYTHON
```

## 步骤耗时 profile（可选）

需要测量哪一步最耗时时，**设环境变量 `MX_PROFILE=1`** 即可：

```bash
MX_PROFILE=1 python3 workflow/mingox.py close-loop --slug <slug>
```

每个步骤会在 stderr 输出一行：

```
[profile] step=close-loop.annotations-gate dur_ms=96 rc=0
[profile] step=close-loop.build dur_ms=116 rc=0
[profile] step=close-loop.validate dur_ms=101 rc=0
[profile] step=close-loop dur_ms=314 rc=0
```

未设 `MX_PROFILE` 时输出完全静默，不影响日常用法。
