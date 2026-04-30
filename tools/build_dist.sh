#!/usr/bin/env bash
#
# 构建 ./dist —— 仅包含外网读者应该看到的静态资源。
# 通过这个白名单显式 OPT-IN 公开文件,默认排除流水线源码、草稿、内部文档。
#
# 这个脚本同时被:
#   - Makefile `dist` target 调用
#   - edgeone.json 的 buildCommand 调用
#   - workflow/mingox.py deploy 调用
# 调用,确保 EdgeOne 部署的根目录只含 ./dist 内的文件。
#
# 用法: bash tools/build_dist.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST="$ROOT/dist"

# 公开顶层文件(只列读者应该看到的)
PUBLIC_FILES=(
  "index.html"
  "about.html"
  "dahanghai.html"
  "favicon.ico"
)

# 公开顶层目录(读者通过 <a href="posts/..."> 等访问)
PUBLIC_DIRS=(
  "posts"
  "css"
  "js"
  "images"
)

# 清理上次构建
rm -rf "$DIST"
mkdir -p "$DIST"

# 拷贝白名单文件
for f in "${PUBLIC_FILES[@]}"; do
  src="$ROOT/$f"
  if [[ -e "$src" ]]; then
    cp "$src" "$DIST/$f"
  else
    echo "[build_dist] warn: missing $f, skipped" >&2
  fi
done

# 拷贝白名单目录(整目录拷,保留结构)
for d in "${PUBLIC_DIRS[@]}"; do
  src="$ROOT/$d"
  if [[ -d "$src" ]]; then
    # 用 cp -R 而不是 rsync,避免依赖 rsync
    cp -R "$src" "$DIST/$d"
  else
    echo "[build_dist] warn: missing dir $d, skipped" >&2
  fi
done

n_files=$(find "$DIST" -type f | wc -l | tr -d ' ')
n_dirs=$(find "$DIST" -mindepth 1 -type d | wc -l | tr -d ' ')
echo "[build_dist] OK -> $DIST ($n_files files, $n_dirs dirs)"
