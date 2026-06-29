from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..models import Problem, difficulty_label
from ..schemas import RecommendRequest, RecommendResponse, RecommendationOut
from ..state import get_recommender
from ..url_parser import parse_url

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    rec = get_recommender()

    raw = req.url or req.problem_id
    if not raw:
        raise HTTPException(status_code=400, detail="Provide a 'url' or 'problem_id'.")

    platform, problem_id = parse_url(raw)
    if problem_id is None:
        raise HTTPException(status_code=400,
                            detail="Could not parse URL. Use a Codeforces or LeetCode problem URL.")

    target = next((p for p in rec.problems if p.id == problem_id), None)
    note = None

    # Live-fetch fallback for problems not bundled in the dataset.
    if target is None and not settings.use_fallback_only:
        target = await _live_fetch(platform, problem_id)
        if target is not None:
            note = ("This problem wasn't in the bundled dataset; it was fetched live and "
                    "embedded on the fly (structural half approximated).")

    if target is None:
        # offer closest matches by title so the UI can guide the user
        suggestions = rec.search(_slug(problem_id), limit=5)
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Problem not found in dataset.",
                "suggestions": [
                    {"id": s.id, "platform": s.platform, "title": s.title, "url": s.url}
                    for s in suggestions
                ],
            },
        )

    recs = rec.recommend(target, top_k=req.top_k)
    return RecommendResponse(
        target={
            "id": target.id, "platform": target.platform, "title": target.title,
            "url": target.url, "tags": target.tags,
            "difficulty": difficulty_label(target.rating_unified),
            "rating": target.rating_unified,
        },
        recommendations=[
            RecommendationOut(
                id=r.id, platform=r.platform, title=r.title, url=r.url, tags=r.tags,
                difficulty=r.difficulty, rating=r.rating_unified,
                similarity=r.similarity, reason=r.reason,
            )
            for r in recs
        ],
        note=note,
    )


async def _live_fetch(platform: str | None, problem_id: str):
    try:
        if platform == "codeforces":
            rest = problem_id.split("cf:", 1)[1]
            contest, index = rest.split("/", 1)
            from ..scraper.codeforces import fetch_one_codeforces
            return await fetch_one_codeforces(contest, index)
        if platform == "leetcode":
            slug = problem_id.split("lc:", 1)[1].strip("/")
            from ..scraper.leetcode import fetch_one_leetcode
            return await fetch_one_leetcode(slug)
    except Exception:  # noqa: BLE001
        return None
    return None


def _slug(problem_id: str) -> str:
    return problem_id.split(":", 1)[-1].replace("/", " ")
