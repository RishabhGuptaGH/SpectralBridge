"""LeetCode scraper.

Uses the problemsetQuestionList GraphQL query. LeetCode difficulties are mapped
to a numeric scale, then shifted: R_unified = R_lc - 400 (per project spec).
"""
from __future__ import annotations

import httpx

from ..config import settings
from ..models import Problem, LEETCODE_NATIVE_RATING
from .http_client import RateLimitedClient

_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug limit: $limit skip: $skip filters: $filters
  ) {
    total: totalNum
    questions: data {
      questionFrontendId title titleSlug difficulty
      topicTags { name }
    }
  }
}
"""


async def fetch_leetcode(limit: int | None = None) -> list[Problem]:
    client = RateLimitedClient(base_delay=1.2)  # LeetCode is stricter -> bigger gap
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/problemset/",
    }
    page = 50
    problems: list[Problem] = []
    async with httpx.AsyncClient(timeout=settings.http_timeout, headers=headers) as http:
        skip = 0
        while True:
            payload = {
                "query": _QUERY,
                "variables": {"categorySlug": "", "skip": skip, "limit": page, "filters": {}},
            }
            data = await client.post_json(http, settings.lc_graphql_url, json=payload)
            qs = (data.get("data", {}) or {}).get("problemsetQuestionList", {}) or {}
            questions = qs.get("questions", []) or []
            if not questions:
                break
            for q in questions:
                slug = q.get("titleSlug")
                if not slug:
                    continue
                diff = q.get("difficulty", "Easy")
                raw = LEETCODE_NATIVE_RATING.get(diff)
                unified = (raw - 400.0) if raw is not None else None
                tags = [t["name"] for t in (q.get("topicTags") or [])]
                title = q.get("title", "")
                problems.append(Problem(
                    id=f"lc:{slug}",
                    platform="leetcode",
                    title=title,
                    url=f"https://leetcode.com/problems/{slug}/",
                    tags=tags,
                    difficulty=diff,
                    rating_raw=raw,
                    rating_unified=unified,
                    text=title,
                    frontend_id=str(q.get("questionFrontendId", "")),
                ))
                if limit and len(problems) >= limit:
                    return problems
            skip += page
            if skip >= qs.get("total", 0):
                break
    return problems


_SINGLE_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId title titleSlug difficulty
    topicTags { name }
  }
}
"""


async def fetch_one_leetcode(slug: str) -> Problem | None:
    client = RateLimitedClient(base_delay=1.0)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/problemset/",
    }
    payload = {"query": _SINGLE_QUERY, "variables": {"titleSlug": slug}}
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout, headers=headers) as http:
            data = await client.post_json(http, settings.lc_graphql_url, json=payload)
    except Exception:  # noqa: BLE001
        return None
    q = (data.get("data", {}) or {}).get("question") or {}
    if not q:
        return None
    diff = q.get("difficulty", "Easy")
    raw = LEETCODE_NATIVE_RATING.get(diff)
    unified = (raw - 400.0) if raw is not None else None
    tags = [t["name"] for t in (q.get("topicTags") or [])]
    title = q.get("title", slug)
    return Problem(
        id=f"lc:{slug}",
        platform="leetcode",
        title=title,
        url=f"https://leetcode.com/problems/{slug}/",
        tags=tags,
        difficulty=diff,
        rating_raw=raw,
        rating_unified=unified,
        text=title,
        frontend_id=str(q.get("questionFrontendId", "")),
    )
