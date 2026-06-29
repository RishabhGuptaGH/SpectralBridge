"""Build the unified problem dataset.

Fetches real data from the Codeforces + LeetCode APIs (with rate-limit
backoff), normalizes ratings to a single unified scale, persists to SQLite,
and also writes a self-contained ``fallback_dataset.json`` so the application
runs with *zero* network access (essential for the hosted demo).

Usage:
    python -m scripts.build_dataset [--cf-limit 2000] [--lc-limit 1000]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

# allow `python scripts/build_dataset.py` and `python -m scripts.build_dataset`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.config import settings
from app.database import upsert_problems
from app.models import Problem, LEETCODE_NATIVE_RATING
from app.scraper.codeforces import fetch_codeforces
from app.scraper.leetcode import fetch_leetcode


def sample_balanced_codeforces(problems: list[Problem], per_bucket: int,
                               seed: int = 42) -> list[Problem]:
    """Take a rating-balanced sample so every difficulty is well represented."""
    rng = random.Random(seed)
    buckets: dict[float, list[Problem]] = defaultdict(list)
    for p in problems:
        if p.rating_unified is not None:
            buckets[p.rating_unified].append(p)
    out: list[Problem] = []
    for rating in sorted(buckets):
        group = buckets[rating]
        rng.shuffle(group)
        out.extend(group[:per_bucket])
    return out


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cf-limit", type=int, default=2000,
                        help="approx. total Codeforces problems to keep")
    parser.add_argument("--lc-limit", type=int, default=1200,
                        help="approx. total LeetCode problems to keep")
    parser.add_argument("--cf-only", action="store_true", help="skip LeetCode")
    parser.add_argument("--lc-only", action="store_true", help="skip Codeforces")
    args = parser.parse_args()

    all_problems: list[Problem] = []

    if not args.lc_only:
        print("[CF] fetching problemset from Codeforces API ...")
        try:
            cf = await fetch_codeforces()
            # how many rating buckets ~ 28 (800..3500 step 100) -> per_bucket
            per_bucket = max(1, args.cf_limit // 30)
            cf = sample_balanced_codeforces(cf, per_bucket)
            print(f"[CF] kept {len(cf)} balanced problems")
            all_problems.extend(cf)
        except Exception as exc:  # noqa: BLE001
            print(f"[CF] fetch failed: {exc!r}")

    if not args.cf_only:
        print("[LC] fetching problemset from LeetCode GraphQL ...")
        try:
            lc = await fetch_leetcode(limit=args.lc_limit)
            print(f"[LC] fetched {len(lc)} problems")
            all_problems.extend(lc)
        except Exception as exc:  # noqa: BLE001
            print(f"[LC] fetch failed: {exc!r}")

    if not all_problems:
        print("No problems fetched. Aborting.")
        return

    # de-dup by id, keep only rated+tagged
    seen, dedup = set(), []
    for p in all_problems:
        if p.id in seen or p.rating_unified is None or not p.tags:
            continue
        seen.add(p.id)
        dedup.append(p)

    print(f"[DB] upserting {len(dedup)} problems into SQLite ...")
    n = upsert_problems(dedup)
    print(f"[DB] wrote {n} rows -> {settings.db_path}")

    fallback = settings.fallback_dataset_path
    with open(fallback, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in dedup], f)
    size_mb = fallback.stat().st_size / 1e6
    print(f"[FS] wrote fallback dataset -> {fallback} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
