"""Train the LSA + spectral pipeline and persist artifacts.

Usage:
    python -m scripts.train_models
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.data_loader import load_problems
from app.ml.recommender import Recommender


def main():
    print(f"[load] db={settings.db_path} fallback={settings.fallback_dataset_path}")
    problems = load_problems()
    print(f"[load] {len(problems)} problems available")

    usable = [p for p in problems if p.rating_unified is not None and p.tags]
    platforms = {}
    for p in usable:
        platforms[p.platform] = platforms.get(p.platform, 0) + 1
    print(f"[load] usable (rated + tagged): {len(usable)}  by platform: {platforms}")

    rec = Recommender()
    t0 = time.time()
    rec.fit(usable)
    print(f"[fit] trained in {time.time() - t0:.2f}s  "
          f"LSA dim={rec.lsa.dim}  fused matrix={rec.matrix.shape}")

    rec.save()
    print(f"[save] artifacts -> {settings.artifacts_dir}")

    # sanity check: pick a known rated problem and show its bridge recommendations
    sample = next((p for p in usable if p.platform == "codeforces"
                   and p.rating_unified and 1500 <= p.rating_unified <= 1900), usable[0])
    print(f"\n[probe] target = {sample.platform}:{sample.id} "
          f"\"{sample.title}\" rating={sample.rating_unified}")
    for r in rec.recommend(sample):
        print(f"   - [{r.platform}] {r.title}  rating={r.rating_unified}  "
              f"sim={r.similarity}  ({r.reason})")


if __name__ == "__main__":
    main()
