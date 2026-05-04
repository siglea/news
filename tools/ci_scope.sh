#!/usr/bin/env bash
#
# 分层 CI: 按 git diff 决定跑哪些检查,日常迭代不用每次都全量 make ci。
#
# 规则:
#   util/*.py 或 workflow/*.py 或 workflow/tests/*.py 改动 → make test + make validate
#   posts/* 或 index.html 或 tools/* 改动 → make validate
#   content/drafts/* 改动 → make validate(覆盖 annotations + posts)
#   仅 *.md 或 docs/* 改动 → 跳过(纯文档无需 CI)
#   其它 → 默认 make validate(保守)
#
# 调用:
#   bash tools/ci_scope.sh            # 默认 vs origin/master
#   bash tools/ci_scope.sh --staged   # 仅看已 staged 的改动
#
# **合并前的全量保险**:CI runner 或人工合并前仍跑 `make ci`(此脚本不替代 ci)。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

MODE="diff"
if [[ "${1:-}" == "--staged" ]]; then
  MODE="staged"
fi

# 收集 changed files
if [[ "$MODE" == "staged" ]]; then
  CHANGED=$(git diff --name-only --cached 2>/dev/null || true)
else
  if git rev-parse --verify origin/master >/dev/null 2>&1; then
    BASE=$(git merge-base HEAD origin/master 2>/dev/null || echo HEAD~1)
  else
    BASE="HEAD~1"
  fi
  CHANGED=$(git diff --name-only "$BASE" 2>/dev/null || true)
fi

if [[ -z "$CHANGED" ]]; then
  echo "[ci-scope] 无变更检测到 (mode=$MODE);默认跑 make validate" >&2
  exec make validate
fi

echo "[ci-scope] mode=$MODE,变更文件:" >&2
echo "$CHANGED" | sed 's/^/  /' >&2

# 决定跑什么
NEEDS_TEST=0
NEEDS_VALIDATE=0
HAS_NON_DOC=0

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  case "$f" in
    util/*.py|workflow/*.py|workflow/tests/*.py)
      NEEDS_TEST=1
      NEEDS_VALIDATE=1
      HAS_NON_DOC=1
      ;;
    posts/*|index.html|about.html|dahanghai.html|tools/*|Makefile|edgeone.json|_config.yml)
      NEEDS_VALIDATE=1
      HAS_NON_DOC=1
      ;;
    content/drafts/*)
      NEEDS_VALIDATE=1
      HAS_NON_DOC=1
      ;;
    *.md|docs/*)
      # Doc-only 不需要 CI 门禁
      :
      ;;
    *)
      # 其它(.gitignore / .coze / 配置等)默认走 validate 兜底
      NEEDS_VALIDATE=1
      HAS_NON_DOC=1
      ;;
  esac
done <<< "$CHANGED"

if [[ "$HAS_NON_DOC" == "0" ]]; then
  echo "[ci-scope] 仅文档改动 → 跳过 CI(合并前请跑 'make ci' 兜底)" >&2
  exit 0
fi

# 顺序执行需要的 target
RC=0
if [[ "$NEEDS_TEST" == "1" ]]; then
  echo "[ci-scope] python 源码改动 → make test" >&2
  make test || RC=$?
  if [[ "$RC" != "0" ]]; then
    echo "[ci-scope] make test FAIL (rc=$RC),停止" >&2
    exit "$RC"
  fi
fi
if [[ "$NEEDS_VALIDATE" == "1" ]]; then
  echo "[ci-scope] 内容/配置改动 → make validate" >&2
  make validate || RC=$?
fi

if [[ "$RC" == "0" ]]; then
  echo "[ci-scope] OK (合并前请用 'make ci' 跑全量兜底)" >&2
fi
exit "$RC"
