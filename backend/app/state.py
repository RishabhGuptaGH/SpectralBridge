"""Process-wide singleton holding the loaded Recommender.

On startup we prefer pre-built artifacts (fast). If they are missing we train
from the available dataset so the service is always usable.
"""
from __future__ import annotations

import logging
import time

from .config import settings
from .data_loader import load_problems
from .ml.recommender import Recommender

logger = logging.getLogger("spectralbridge")

recommender: Recommender | None = None


def get_recommender() -> Recommender:
    if recommender is None:
        raise RuntimeError("Recommender not initialized")
    return recommender


def initialize() -> Recommender:
    global recommender
    t0 = time.time()
    try:
        recommender = Recommender.load()
        logger.info("Loaded pre-trained artifacts in %.2fs", time.time() - t0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load artifacts (%s); training from dataset.", exc)
        problems = load_problems()
        usable = [p for p in problems if p.rating_unified is not None and p.tags]
        recommender = Recommender().fit(usable)
        try:
            recommender.save()
        except Exception as save_exc:  # noqa: BLE001
            logger.warning("Could not persist artifacts: %s", save_exc)
        logger.info("Trained recommender in %.2fs", time.time() - t0)
    return recommender
