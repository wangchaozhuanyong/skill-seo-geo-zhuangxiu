#!/usr/bin/env python3
"""CLI wrapper for pre-publish SEO/GEO content QA."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SEO_GEO_DIR = SCRIPT_DIR / "seo_geo"
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from qa import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
