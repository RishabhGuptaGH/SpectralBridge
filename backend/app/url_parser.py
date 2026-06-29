"""Parse Codeforces / LeetCode URLs into canonical problem ids."""
from __future__ import annotations

import re

# Codeforces accepts several URL shapes:
#   .../problemset/problem/1234/A
#   .../contest/1234/problem/A
#   .../problem/1234/A   (gym)
_CF_PATTERNS = [
    re.compile(r"codeforces\.com/.*?problem/(\d+)/([A-Za-z]\d?)"),
    re.compile(r"codeforces\.com/contest/(\d+)/problem/([A-Za-z]\d?)"),
    re.compile(r"codeforces\.com/gym/(\d+)/problem/([A-Za-z]\d?)"),
]

# LeetCode:
#   .../problems/two-sum/
#   .../problems/two-sum/description/
_LC_PATTERN = re.compile(r"leetcode\.com/problems/([a-z0-9\-]+)/")


def parse_url(url: str) -> tuple[str | None, str | None]:
    """Return (platform, problem_id) or (None, None) if not recognized."""
    if not url:
        return None, None
    text = url.strip()

    # accept a bare "cf:1234/A" or "lc:two-sum" id directly
    if text.startswith("cf:"):
        return "codeforces", text
    if text.startswith("lc:"):
        return "leetcode", text

    for pat in _CF_PATTERNS:
        m = pat.search(text)
        if m:
            contest, index = m.group(1), m.group(2).upper()
            return "codeforces", f"cf:{contest}/{index}"

    m = _LC_PATTERN.search(text)
    if m:
        return "leetcode", f"lc:{m.group(1)}"

    return None, None
