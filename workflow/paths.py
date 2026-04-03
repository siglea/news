"""Repository root resolution for workflow scripts."""
from __future__ import annotations

from pathlib import Path

WORKFLOW_DIR = Path(__file__).resolve().parent
ROOT = WORKFLOW_DIR.parent
CONTENT_DRAFTS = ROOT / "content" / "drafts"
UTIL_DIR = ROOT / "util"
