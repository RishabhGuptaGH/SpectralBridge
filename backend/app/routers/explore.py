from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..models import difficulty_label
from ..schemas import ProblemOut
from ..state import get_recommender

router = APIRouter(prefix="/api", tags=["explore"])


def _to_out(problem) -> ProblemOut:
    return ProblemOut(
        id=problem.id, platform=problem.platform, title=problem.title, url=problem.url,
        tags=problem.tags, difficulty=difficulty_label(problem.rating_unified),
        rating=problem.rating_unified,
    )


@router.get("/search", response_model=list[ProblemOut])
def search(q: str = Query(..., min_length=1), limit: int = Query(12, ge=1, le=50)):
    rec = get_recommender()
    results = rec.search(q, limit=limit)
    return [_to_out(p) for p in results]


@router.get("/problem/{problem_id}", response_model=ProblemOut)
def get_problem(problem_id: str):
    rec = get_recommender()
    p = next((x for x in rec.problems if x.id == problem_id), None)
    if p is None:
        raise HTTPException(status_code=404, detail="Problem not found in dataset")
    return _to_out(p)


@router.get("/random", response_model=list[ProblemOut])
def random(limit: int = Query(6, ge=1, le=30)):
    import random as _r
    rec = get_recommender()
    sample = _r.sample(rec.problems, min(limit, len(rec.problems)))
    return [_to_out(p) for p in sample]
