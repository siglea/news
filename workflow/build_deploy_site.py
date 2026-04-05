#!/usr/bin/env python3
"""
Assemble a minimal static tree into site/ for EdgeOne Pages deploy.

The EdgeOne builder otherwise copies the entire repo (workspace, util, node_modules
under extensions, etc.) and can exceed the project's file count limit.
Only public MingoX assets are copied: root HTML, posts/, css/, js/, images/.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Optional root files (copy if present)
_ROOT_FILES = (
    "index.html",
    "about.html",
    "dahanghai.html",
    "_config.yml",
    "LICENSE",
    "README.md",
    "update-check.json",
)

_DIRS = ("css", "js", "images", "posts")


def main() -> int:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    for name in _ROOT_FILES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, SITE / name)

    for d in _DIRS:
        src = ROOT / d
        if src.is_dir():
            shutil.copytree(src, SITE / d)
        else:
            print(f"[build_deploy_site] warn: missing directory {src}", file=sys.stderr)

    n = sum(1 for p in SITE.rglob("*") if p.is_file())
    print(f"[build_deploy_site] wrote {SITE} ({n} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
