from __future__ import annotations

from fastapi import APIRouter

from ..models import difficulty_label
from ..state import get_recommender
from ..schemas import StatsOut

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    rec = get_recommender()
    return {"status": "ok", "problems": len(rec.problems)}


@router.get("/stats", response_model=StatsOut)
def stats():
    rec = get_recommender()
    cf = sum(1 for p in rec.problems if p.platform == "codeforces")
    lc = sum(1 for p in rec.problems if p.platform == "leetcode")
    ratings = [p.rating_unified for p in rec.problems if p.rating_unified is not None]
    tags = set()
    for p in rec.problems:
        tags.update(p.tags)
    return StatsOut(
        total=len(rec.problems),
        codeforces=cf,
        leetcode=lc,
        lsa_dimensions=rec.lsa.dim,
        fused_dimensions=int(rec.matrix.shape[1]),
        rating_min=min(ratings) if ratings else None,
        rating_max=max(ratings) if ratings else None,
        tag_count=len(tags),
    )


@router.get("/tags")
def tags():
    rec = get_recommender()
    counts: dict[str, int] = {}
    for p in rec.problems:
        for t in p.tags:
            counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: -x[1])[:40]
    return [{"tag": t, "count": c} for t, c in ranked]
