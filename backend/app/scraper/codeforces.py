"""Codeforces scraper.

Uses the official problemset.problems endpoint. Codeforces ratings are the
*reference* scale, so R_unified = R_cf (no shift).
"""
from __future__ import annotations

import httpx

from ..config import settings
from ..models import Problem
from .http_client import RateLimitedClient


async def fetch_codeforces(limit: int | None = None) -> list[Problem]:
    client = RateLimitedClient(base_delay=0.6)
    headers = {"User-Agent": "SpectralBridge/1.0 (+https://leetcode.com)"}
    async with httpx.AsyncClient(timeout=settings.http_timeout, headers=headers) as http:
        data = await client.get_json(http, f"{settings.cf_api_base}/problemset.problems")
        raw = data.get("result", {}).get("problems", [])

    problems: list[Problem] = []
    for p in raw:
        contest = p.get("contestId")
        index = p.get("index")
        if not contest or not index:
            continue
        if p.get("type") and p["type"] != "PROGRAMMING":
            continue
        rating = p.get("rating")  # may be None
        tags = p.get("tags", []) or []
        title = p.get("name", "")
        problems.append(Problem(
            id=f"cf:{contest}/{index}",
            platform="codeforces",
            title=title,
            url=f"https://codeforces.com/problemset/problem/{contest}/{index}",
            tags=tags,
            difficulty=str(rating) if rating else "Unrated",
            rating_raw=float(rating) if rating else None,
            rating_unified=float(rating) if rating else None,
            text=title,  # statement not exposed by this endpoint; tags carry signal
            contest_id=str(contest),
            index=index,
        ))
        if limit and len(problems) >= limit:
            break
    return problems


_CACHE: list[Problem] | None = None


async def fetch_one_codeforces(contest: str, index: str) -> Problem | None:
    """Look up a single Codeforces problem by contest id + index."""
    global _CACHE
    target = f"cf:{contest}/{index.upper()}"
    if _CACHE is None:
        _CACHE = await fetch_codeforces()
    for p in _CACHE:
        if p.id == target:
            return p
    return None
