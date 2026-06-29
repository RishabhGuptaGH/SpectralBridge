from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Problem:
    """Unified representation of a problem from either platform."""

    id: str                       # canonical id, e.g. "cf:1200/A" or "lc:two-sum"
    platform: str                 # "codeforces" | "leetcode"
    title: str
    url: str
    tags: list[str]               # normalized, lowercase algorithmic tags
    difficulty: str               # human-readable ("800", "Easy", ...)
    rating_raw: Optional[float]   # platform-native numeric rating (None if unknown)
    rating_unified: Optional[float]  # cross-platform normalized rating
    text: str                     # cleaned statement / description used for LSA
    contest_id: Optional[str] = None
    index: Optional[str] = None
    frontend_id: Optional[str] = None  # LeetCode question number, e.g. "1"

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# LeetCode difficulty -> numeric mapping.
#
# LeetCode's public problemset API exposes only Easy/Medium/Hard. We project
# those onto a Codeforces-style scale BEFORE applying the R_unified = R_lc - 400
# shift specified in the project. The chosen native values map cleanly onto the
# CF ranges they correspond to (Easy ~ 800-1200, Medium ~ 1400-1900, Hard ~ 2100+).
# ---------------------------------------------------------------------------
LEETCODE_NATIVE_RATING = {
    "Easy": 1300.0,
    "Medium": 1900.0,
    "Hard": 2500.0,
}


def difficulty_label(rating_unified: Optional[float]) -> str:
    """Human label for a unified rating, used in the UI."""
    if rating_unified is None:
        return "Unrated"
    if rating_unified < 1200:
        return "Easy"
    if rating_unified < 1800:
        return "Medium"
    return "Hard"
