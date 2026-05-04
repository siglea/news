# MingoX 本地 / CI 入口
#
# 默认 PYTHON 是 `python3`；建议在 .venv 里用,或显式覆盖:
#   make test PYTHON=.venv/bin/python
#
# 主要 target:
#   test                 单元测试(workflow/tests/test_*.py)
#   validate-annotations 草稿标注质量门禁(content/drafts/**/llm_annotations.json)
#   validate-posts       成稿版式校验(posts/*.html)
#   validate             以上两项
#   ci                   test + validate(合并前全量推荐入口)
#   ci-scope             按 git diff 决定跑啥(日常迭代推荐;委托 tools/ci_scope.sh)
#   dist                 构建 ./dist 公开站点目录(白名单 opt-in,不含 drafts/源码)
#   clean                清理 ./dist
#   help                 显示本说明

PYTHON ?= python3

.PHONY: help test validate-annotations validate-posts validate ci ci-scope dist clean

help:
	@echo "MingoX targets:"
	@echo "  make test                 — run workflow/tests/test_*.py via unittest"
	@echo "  make validate-annotations — gate llm_annotations.json across drafts"
	@echo "  make validate-posts       — check posts/*.html layout"
	@echo "  make validate             — annotations + posts"
	@echo "  make ci                   — test + validate (合并前全量推荐)"
	@echo "  make ci-scope             — 按 git diff 决定跑啥 (日常迭代推荐)"
	@echo "  make dist                 — build ./dist (whitelist: 仅外网应见的静态资源)"
	@echo "  make clean                — remove ./dist"
	@echo ""
	@echo "Override Python:  make test PYTHON=.venv/bin/python"

test:
	$(PYTHON) -m unittest discover -s workflow/tests -p 'test_*.py' -t . -v

validate-annotations:
	$(PYTHON) workflow/mingox.py validate --annotations

validate-posts:
	$(PYTHON) workflow/mingox.py validate

validate: validate-annotations validate-posts

ci: test validate
	@echo "[ci] OK — all checks passed"

ci-scope:
	bash tools/ci_scope.sh

dist:
	bash tools/build_dist.sh

clean:
	rm -rf dist
