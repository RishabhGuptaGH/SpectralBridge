"""Unified dataset loader.

Resolution order:
  1. SQLite database (if non-empty)
  2. bundled fallback_dataset.json (zero-network fallback for hosted demo)
  3. live scrape from the platform APIs
"""
from __future__ import annotations

import json

from .config import settings
from .database import load_all_problems, count_problems
from .models import Problem
from .scraper.codeforces import fetch_codeforces
from .scraper.leetcode import fetch_leetcode


def load_problems(live_fallback: bool = False, cf_limit: int = 2000,
                  lc_limit: int = 1200) -> list[Problem]:
    if count_problems() > 0:
        return load_all_problems()

    if settings.fallback_dataset_path.exists():
        with open(settings.fallback_dataset_path, encoding="utf-8") as f:
            return [Problem(**p) for p in json.load(f)]

    if live_fallback and not settings.use_fallback_only:
        import asyncio
        async def _scrape():
            return await fetch_codeforces(limit=cf_limit) + await fetch_leetcode(limit=lc_limit)
        return asyncio.run(_scrape())

    raise RuntimeError("No problem data available (DB empty, no fallback file, scrape disabled).")
