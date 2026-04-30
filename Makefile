# MingoX 本地 / CI 入口
#
# 默认 PYTHON 是 `python3`；建议在 .venv 里用,或显式覆盖:
#   make test PYTHON=.venv/bin/python
#
# 主要 target:
#   test                 单元测试(workflow/test_*.py)
#   validate-annotations 草稿标注质量门禁(content/drafts/**/llm_annotations.json)
#   validate-posts       成稿版式校验(posts/*.html)
#   validate             以上两项
#   ci                   test + validate(CI 推荐入口)
#   help                 显示本说明

PYTHON ?= python3

.PHONY: help test validate-annotations validate-posts validate ci

help:
	@echo "MingoX targets:"
	@echo "  make test                 — run workflow/test_*.py via unittest"
	@echo "  make validate-annotations — gate llm_annotations.json across drafts"
	@echo "  make validate-posts       — check posts/*.html layout"
	@echo "  make validate             — annotations + posts"
	@echo "  make ci                   — test + validate (推荐 CI 入口)"
	@echo ""
	@echo "Override Python:  make test PYTHON=.venv/bin/python"

test:
	$(PYTHON) -m unittest discover -s workflow -p 'test_*.py' -v

validate-annotations:
	$(PYTHON) workflow/mingox.py validate --annotations

validate-posts:
	$(PYTHON) workflow/mingox.py validate

validate: validate-annotations validate-posts

ci: test validate
	@echo "[ci] OK — all checks passed"
