"""Phase 4 - Fusion and the *Bridge* filter.

Fuses the semantic (LSA) and structural (spectral) embeddings into a single
unit vector per problem, then recommends *bridge* problems: slightly easier
problems that reuse the exact same algorithmic logic.

    target_rating - bridge_upper <= candidate_unified <= target_rating - bridge_lower

The two halves (semantic / structural) are individually L2-normalized before
concatenation, so they contribute *equally* to the fused cosine similarity.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import joblib
import numpy as np
from sklearn.preprocessing import normalize

from ..config import settings
from ..models import Problem, difficulty_label
from .lsa import LSAEncoder
from .preprocessing import build_corpus, graph_tags, normalize_tags
from .spectral import SpectralEmbedder


@dataclass
class Recommendation:
    id: str
    platform: str
    title: str
    url: str
    tags: list[str]
    difficulty: str
    rating_unified: float | None
    similarity: float
    reason: str


class Recommender:
    """Trains the full pipeline and serves bridge recommendations."""

    def __init__(self):
        self.problems: list[Problem] = []
        self.lsa = LSAEncoder()
        self.spectral = SpectralEmbedder()
        self.matrix: np.ndarray | None = None      # fused, L2-normalized (N, D)
        self.id_to_idx: dict[str, int] = {}
        self._fitted = False

    # ----------------------------------------------------------------- fit
    def fit(self, problems: list[Problem]) -> "Recommender":
        problems = [p for p in problems if p.rating_unified is not None and p.tags]
        if len(problems) < 4:
            raise ValueError("Need at least 4 rated, tagged problems to train.")

        self.problems = problems
        self.id_to_idx = {p.id: i for i, p in enumerate(problems)}

        # --- Phase 2: LSA over tag-boosted corpus ---
        corpus = [build_corpus(p.text, p.tags) for p in problems]
        semantic = self.lsa.fit(corpus)

        # --- Phase 3: spectral embedding ---
        g_tags = [graph_tags(p.tags) for p in problems]
        ratings = [p.rating_unified for p in problems]
        structural = self.spectral.fit(g_tags, ratings, semantic)

        # --- Phase 4: fusion ---
        fused = np.hstack([semantic, structural]).astype(np.float64)
        fused = normalize(fused)  # global L2 normalization
        self.matrix = fused
        self._fitted = True
        return self

    # -------------------------------------------------------------- query
    def recommend(self, target: Problem, top_k: int | None = None) -> list[Recommendation]:
        if not self._fitted or self.matrix is None:
            raise RuntimeError("Recommender is not fitted.")

        idx = self.id_to_idx.get(target.id)
        if idx is not None:
            target_vec = self.matrix[idx]            # exact precomputed fused vector
        else:
            target_vec = self._vectorize_single(target)  # unseen problem
        sims = self.matrix @ target_vec

        if idx is not None:
            sims[idx] = -np.inf  # never recommend the problem itself

        order = np.argsort(-sims)
        return self._select_bridges(order, sims, target, top_k or settings.bridge_top_k, idx)

    # ---------------------------------------------------- internal helpers
    def _vectorize_single(self, target: Problem) -> np.ndarray:
        """Build the fused vector for an arbitrary (possibly unseen) problem.

        The LSA half comes from the fitted encoder. A single new node has a
        trivial spectrum, so its structural half is zero-padded to match the
        fused dimensionality; the dominant tag-boosted semantic signal still
        drives the recommendation. (DB problems always use their exact
        precomputed vector instead.)
        """
        corpus = build_corpus(target.text, target.tags)
        semantic = self.lsa.transform([corpus])[0]
        structural_dim = self.matrix.shape[1] - self.lsa.dim
        structural = np.zeros(structural_dim, dtype=np.float64)
        fused = np.concatenate([semantic, structural])
        norm = np.linalg.norm(fused)
        if norm:
            fused = fused / norm
        return fused

    def _select_bridges(self, order, sims, target, top_k, skip_idx) -> list[Recommendation]:
        """Select `top_k` recommendations.

        Two stages:
          1. Gather a generous *candidate pool* that satisfies the difficulty
             window (strict → relaxed → rating-band fallback). The pool is built
             **per-platform** so that LeetCode candidates (which often have lower
             fused similarity than Codeforces ones) are never squeezed out by a
             global similarity cap.
          2. Pick the final set with **platform diversity**: every result set is
             guaranteed to contain at least one Codeforces AND one LeetCode
             problem whenever both are available in the pool.
        """
        target_rating = target.rating_unified
        lower, upper = settings.bridge_lower, settings.bridge_upper
        PER_PLATFORM = 20
        platforms = sorted({p.platform for p in self.problems})

        pool: list[int] = []
        pool_ids: set[int] = set()
        reasons: dict[int, str] = {}

        def gather(predicate, reason):
            """For each platform, append up to PER_PLATFORM candidates (best
            similarity first) matching predicate that aren't already in pool."""
            for plat in platforms:
                added = 0
                for i in order:
                    if added >= PER_PLATFORM:
                        break
                    if i == skip_idx or i in pool_ids:
                        continue
                    if self.problems[i].platform != plat:
                        continue
                    if predicate(i):
                        pool.append(i)
                        pool_ids.add(i)
                        reasons[i] = reason
                        added += 1

        def per_platform_count(plat):
            return sum(1 for i in pool if self.problems[i].platform == plat)

        # 1) strict bridge window: candidate 100..300 points easier.
        def in_strict(i):
            r = self.problems[i].rating_unified
            return r is not None and (target_rating - upper) <= r <= (target_rating - lower)
        gather(in_strict, "bridge")

        # 2) relaxed window: widen the band in BOTH directions so it also covers
        #    targets near the rating floor/ceiling (where no easier problem exists).
        #    IMPORTANT: keep widening until EACH platform has enough candidates —
        #    LeetCode only exists at 3 discrete ratings (900/1500/2100), so a CF
        #    target like 1500 needs the window widened past 1450 to reach LC@1500.
        for expand in (50, 150, 300, 500):
            if all(per_platform_count(pl) >= PER_PLATFORM for pl in platforms):
                break
            lo_delta, hi_delta = upper + expand, lower - expand
            def in_relaxed(i, lo_delta=lo_delta, hi_delta=hi_delta):
                r = self.problems[i].rating_unified
                return r is not None and (target_rating - lo_delta) <= r <= (target_rating - hi_delta)
            gather(in_relaxed, "bridge-relaxed")

        # 3) last resort: most-similar problems within a rating neighbourhood.
        #    Asymmetric band: prefer EASIER problems (the bridge promise), with
        #    only a small upward slack so we don't suggest a much-harder one.
        band = 600
        def in_band(i):
            r = self.problems[i].rating_unified
            return r is not None and (target_rating - band) <= r <= (target_rating + 150)
        gather(in_band, "nearest")

        # absolute fallback (extremely rare): pure similarity, any rating.
        if len(pool) < top_k * len(platforms):
            gather(lambda i: self.problems[i].rating_unified is not None, "nearest")

        chosen = self._select_with_diversity(pool, top_k, platforms)
        # rank the final set by similarity (best match first)
        chosen.sort(key=lambda i: -sims[i])

        results: list[Recommendation] = []
        for i in chosen:
            p = self.problems[i]
            results.append(Recommendation(
                id=p.id, platform=p.platform, title=p.title, url=p.url,
                tags=normalize_tags(p.tags), difficulty=difficulty_label(p.rating_unified),
                rating_unified=p.rating_unified, similarity=round(float(sims[i]), 4),
                reason=reasons.get(i, "nearest"),
            ))
        return results

    def _select_with_diversity(self, pool: list[int], top_k: int,
                               platforms: list[str]) -> list[int]:
        """Pick `top_k` from a similarity-ordered `pool`, guaranteeing that both
        platforms are represented whenever possible."""
        if not pool:
            return []

        chosen: list[int] = []
        chosen_set: set[int] = set()

        def add(i):
            if i in chosen_set:
                return False
            chosen.append(i)
            chosen_set.add(i)
            return True

        # Guarantee one representative per platform (best similarity first).
        for plat in platforms:
            if len(chosen) >= top_k:
                break
            for i in pool:
                if self.problems[i].platform == plat:
                    add(i)
                    break

        # Fill remaining slots with the highest-similarity candidates overall.
        for i in pool:
            if len(chosen) >= top_k:
                break
            add(i)

        return chosen

    # ------------------------------------------------------------ search
    def search(self, query: str, limit: int = 10) -> list[Problem]:
        q = query.strip().lower()
        if not q:
            return []
        scored: list[tuple[float, Problem]] = []
        for p in self.problems:
            hay = (p.title + " " + p.id).lower()
            score = _fuzzy_score(q, hay)
            if score > 0:
                scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:limit]]

    # ----------------------------------------------------------- persist
    def save(self, artifacts_dir=None):
        d = settings.artifacts_dir if artifacts_dir is None else artifacts_dir
        d = os.fspath(d)
        self.lsa.save(os.path.join(d, "lsa.joblib"))
        np.save(os.path.join(d, "fused_matrix.npy"), self.matrix)
        meta = [{
            "id": p.id, "platform": p.platform, "title": p.title, "url": p.url,
            "tags": p.tags, "difficulty": p.difficulty,
            "rating_raw": p.rating_raw, "rating_unified": p.rating_unified,
            "text": p.text, "contest_id": p.contest_id, "index": p.index,
            "frontend_id": p.frontend_id,
        } for p in self.problems]
        with open(os.path.join(d, "problems.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)
        with open(os.path.join(d, "version.txt"), "w", encoding="utf-8") as f:
            f.write("1")

    @classmethod
    def load(cls, artifacts_dir=None) -> "Recommender":
        d = settings.artifacts_dir if artifacts_dir is None else artifacts_dir
        d = os.fspath(d)
        rec = cls()
        rec.lsa = LSAEncoder.load(os.path.join(d, "lsa.joblib"))
        rec.matrix = np.load(os.path.join(d, "fused_matrix.npy"))
        with open(os.path.join(d, "problems.json"), encoding="utf-8") as f:
            meta = json.load(f)
        rec.problems = [Problem(**m) for m in meta]
        rec.id_to_idx = {p.id: i for i, p in enumerate(rec.problems)}
        rec._fitted = True
        return rec


def _fuzzy_score(query: str, hay: str) -> float:
    """Tiny relevance score: exact token matches boost the rank."""
    if query in hay:
        return 2.0
    score = 0.0
    for tok in query.split():
        if tok in hay:
            score += 1.0
    return score
