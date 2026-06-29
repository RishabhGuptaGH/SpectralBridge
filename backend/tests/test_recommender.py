import numpy as np
import pytest

from app.models import Problem
from app.ml.recommender import Recommender


def _mk(pid, platform, title, tags, rating, text=None):
    return Problem(
        id=pid, platform=platform, title=title,
        url=f"https://x/{pid}", tags=tags, difficulty=str(rating),
        rating_raw=float(rating), rating_unified=float(rating),
        text=text or title,
    )


@pytest.fixture(scope="module")
def rec():
    # Two algorithmic clusters spread across a rating ladder.
    bs = [("binary search", "binary-search-group")]
    df = [("dfs", "dfs-group")]
    problems = [
        # binary search cluster
        _mk("cf:bs-800", "codeforces", "BS A", ["binary search"], 800),
        _mk("cf:bs-900", "codeforces", "BS B", ["binary search"], 900),
        _mk("cf:bs-1100", "codeforces", "BS C", ["binary search"], 1100),
        _mk("cf:bs-1300", "codeforces", "BS D", ["binary search"], 1300),
        _mk("cf:bs-1400", "codeforces", "BS E", ["binary search"], 1400),
        _mk("cf:bs-1500", "codeforces", "BS F", ["binary search"], 1500),
        _mk("cf:bs-1700", "codeforces", "BS G hard", ["binary search"], 1700),
        _mk("cf:bs-1900", "codeforces", "BS H harder", ["binary search"], 1900),
        # dfs cluster
        _mk("cf:df-800", "codeforces", "DF A", ["dfs", "graphs"], 800),
        _mk("cf:df-1100", "codeforces", "DF B", ["dfs", "graphs"], 1100),
        _mk("cf:df-1300", "codeforces", "DF C", ["dfs", "graphs"], 1300),
        _mk("cf:df-1500", "codeforces", "DF D", ["dfs", "graphs"], 1500),
        _mk("cf:df-1700", "codeforces", "DF E", ["dfs", "graphs"], 1700),
    ]
    return Recommender().fit(problems)


@pytest.fixture(scope="module")
def mixed_rec():
    # Binary-search cluster on BOTH platforms so diversity can be tested.
    problems = [
        _mk("cf:bs-1500", "codeforces", "CF BS", ["binary search"], 1500),
        _mk("cf:bs-1400", "codeforces", "CF BS2", ["binary search"], 1400),
        _mk("cf:bs-1300", "codeforces", "CF BS3", ["binary search"], 1300),
        _mk("lc:bs-1500", "leetcode", "LC BS", ["Binary Search"], 1500),
        _mk("lc:bs-1400", "leetcode", "LC BS2", ["Binary Search"], 1400),
        _mk("lc:bs-1300", "leetcode", "LC BS3", ["Binary Search"], 1300),
    ]
    return Recommender().fit(problems)


def test_fitted_dimensions(rec):
    assert rec.matrix is not None
    assert rec.matrix.shape[0] == 13
    assert rec.matrix.shape[1] > 0


def test_recommendations_sorted_and_not_self(rec):
    target = next(p for p in rec.problems if p.id == "cf:bs-1700")
    recs = rec.recommend(target, top_k=3)
    sims = [r.similarity for r in recs]
    assert sims == sorted(sims, reverse=True)
    assert all(r.id != target.id for r in recs)


def test_bridge_rating_window_respected(rec):
    from app.config import settings
    target = next(p for p in rec.problems if p.id == "cf:bs-1700")
    recs = rec.recommend(target, top_k=3)
    assert recs, "expected bridge recommendations"
    for r in recs:
        if r.reason == "bridge":
            assert settings.bridge_lower <= (target.rating_unified - r.rating_unified) <= settings.bridge_upper


def test_prefers_same_algorithm(rec):
    target = next(p for p in rec.problems if p.id == "cf:bs-1700")
    recs = rec.recommend(target, top_k=3)
    # the binary-search ladder has 1400 and 1500 in the window -> should dominate
    rec_ids = {r.id for r in recs}
    assert "cf:bs-1400" in rec_ids
    assert "cf:bs-1500" in rec_ids


def test_unit_norm_fused_vectors(rec):
    norms = np.linalg.norm(rec.matrix, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_platform_diversity(mixed_rec):
    # Every recommendation set must include at least one Codeforces AND one
    # LeetCode problem (whenever both are available in the corpus).
    for target in mixed_rec.problems:
        recs = mixed_rec.recommend(target, top_k=3)
        platforms = {r.platform for r in recs}
        assert "codeforces" in platforms, f"missing codeforces for {target.id}"
        assert "leetcode" in platforms, f"missing leetcode for {target.id}"


def test_floor_target_gets_level_appropriate_bridges(rec):
    # rating 800 is at the floor: no easier problems exist. The engine must NOT
    # return arbitrarily-hard look-alikes, must never return the target itself,
    # and must keep recommendations level-appropriate.
    target = next(p for p in rec.problems if p.id == "cf:bs-800")
    recs = rec.recommend(target, top_k=3)
    assert recs
    for r in recs:
        assert r.id != target.id                      # never recommend the target
        assert r.rating_unified <= target.rating_unified + 400  # stays level-appropriate

