"""Text & tag preprocessing.

This module is the heart of the defence against the *Semantic "Story" Problem*.

Codeforces statements bury simple algorithms under elaborate stories ("Farmer
John placing cows in stalls" == binary search). Pure TF-IDF over raw text would
cluster problems by *flavour* (cows vs spaceships) instead of by *algorithm*.

We counter this with three mechanisms, applied in :func:`build_corpus`:

1. **Tag boosting** - the algorithmic tags (the ground-truth signal) are
   repeated ``settings.tag_boost`` times and prepended to the document, so the
   latent LSA space is dominated by algorithmic concepts rather than story
   nouns.

2. **Algorithmic keyword dictionary** - common story vocabulary is mapped to
   canonical algorithmic tokens (e.g. "maze"/"grid" -> "graph", "shortest
   path"/"distance" -> "bfs shortest-path"). This injects structural signal
   even when tags are sparse.

3. **Code stripping** - fenced code blocks and inline math are removed so they
   don't pollute term statistics.
"""
from __future__ import annotations

import re
from typing import Iterable

from ..config import settings

# ---------------------------------------------------------------------------
# Tag normalization: collapse platform-specific synonyms to one canonical tag.
# Covers both Codeforces tags ("dfs and similar") and LeetCode topic tags
# ("Depth-First Search") so the two platforms share one vocabulary - this is
# what makes *cross-platform* bridging actually work.
# ---------------------------------------------------------------------------
TAG_SYNONYMS: dict[str, str] = {
    # graphs / trees
    "dfs and similar": "dfs",
    "depth-first search": "dfs",
    "dfs": "dfs",
    "bfs": "bfs",
    "breadth-first search": "bfs",
    "graphs": "graph",
    "graph": "graph",
    "trees": "tree",
    "tree": "tree",
    "binary tree": "tree",
    "binary search tree": "bst",
    "shortest paths": "shortest-path",
    "shortest path": "shortest-path",
    "dsu": "disjoint-set",
    "disjoint set": "disjoint-set",
    "union find": "disjoint-set",
    "dsu (disjoint set union)": "disjoint-set",
    # math / numbers
    "math": "math",
    "number theory": "number-theory",
    "combinatorics": "combinatorics",
    "probability": "probability",
    "probabilities": "probability",
    "bitmasks": "bit-manipulation",
    "bit manipulation": "bit-manipulation",
    # dp / search
    "dp": "dynamic-programming",
    "dynamic programming": "dynamic-programming",
    "memoization": "dynamic-programming",
    "two pointers": "two-pointers",
    "binary search": "binary-search",
    "meet-in-the-middle": "meet-in-the-middle",
    "interactive": "interactive",
    "constructive algorithms": "constructive",
    "constructive": "constructive",
    "greedy": "greedy",
    "sorting": "sorting",
    "divide and conquer": "divide-and-conquer",
    # strings
    "strings": "string",
    "string": "string",
    "hashing": "hashing",
    "hash table": "hashing",
    "rolling hash": "hashing",
    "string suffix structures": "suffix-structure",
    "trie": "trie",
    # data structures
    "data structures": "data-structure",
    "data structure": "data-structure",
    "geometry": "geometry",
    "games": "game-theory",
    "game theory": "game-theory",
    "flows": "max-flow",
    "maxflow": "max-flow",
    "matrices": "matrix",
    "matrix": "matrix",
    "fft": "fft",
    "ternary search": "ternary-search",
    "expression parsing": "expression-parsing",
    "recursion": "recursion",
    "simulation": "simulation",
    "implementation": "implementation",
    "brute force": "brute-force",
    "sliding window": "sliding-window",
    "heap": "heap-priority-queue",
    "heap priority queue": "heap-priority-queue",
    "priority queue": "heap-priority-queue",
    "monotonic stack": "monotonic-stack",
    "monotonic queue": "monotonic-stack",
    "stack": "stack",
    "queue": "queue",
    "linked list": "linked-list",
    "segment tree": "segment-tree",
    "fenwick tree": "fenwick-tree",
    "binary indexed tree": "fenwick-tree",
    "backtracking": "backtracking",
    "prefix sum": "prefix-sum",
    "counting": "counting",
    "enumeration": "enumeration",
    "design": "design",
    "ordered map": "ordered-map",
}

# Tags that are too generic to be informative for the structural graph.
# They are allowed in the *semantic* corpus (tag-boosted text) but excluded
# from the *adjacency* graph so they don't create spurious dense edges.
GENERIC_TAGS_FOR_GRAPH = {
    "implementation", "math", "constructive", "brute-force", "sorting",
    "greedy", "simulation", "string", "data-structure", "array",
}

# ---------------------------------------------------------------------------
# Algorithmic keyword dictionary: map story vocabulary -> algorithmic tokens.
# This is what lets LSA see through "Farmer John" to "binary-search".
# ---------------------------------------------------------------------------
ALGO_KEYWORD_MAP: dict[str, str] = {
    # search
    "search": "binary-search", "sorted": "binary-search", "monotonic": "binary-search",
    "minimize": "binary-search", "maximize": "binary-search",
    "lower bound": "binary-search", "upper bound": "binary-search",
    # graphs
    "graph": "graph", "tree": "tree", "forest": "tree", "edge": "graph",
    "node": "graph", "vertex": "graph", "adjacency": "graph",
    "neighbor": "graph", "neighbour": "graph",
    # traversal
    "path": "bfs shortest-path", "shortest": "bfs shortest-path",
    "distance": "bfs shortest-path", "maze": "graph", "grid": "graph",
    "traversal": "dfs", "connected": "dfs", "component": "dfs",
    "cycle": "dfs", "bipartite": "dfs",
    # dp
    "subsequence": "dynamic-programming", "states": "dynamic-programming",
    "transition": "dynamic-programming", "optimal substructure": "dynamic-programming",
    "knapsack": "dynamic-programming", "subproblem": "dynamic-programming",
    # greedy / two pointers
    "swap": "greedy", "pair": "two-pointers", "prefix sum": "prefix-sum",
    "subarray": "prefix-sum", "sliding": "sliding-window", "window": "sliding-window",
    # numbers
    "prime": "number-theory", "divisor": "number-theory", "modulo": "number-theory",
    "gcd": "number-theory", "factor": "number-theory", "modular": "number-theory",
    # bits
    "bit": "bit-manipulation", "xor": "bit-manipulation", "mask": "bit-manipulation",
    "subset": "bit-manipulation",
    # sets / dsu
    "merge": "disjoint-set", "union": "disjoint-set", "set": "disjoint-set",
    # data structures
    "stack": "stack", "queue": "queue", "heap": "heap-priority-queue",
    "priority": "heap-priority-queue", "segment": "segment-tree",
    # strings
    "palindrome": "string", "substring": "string", "anagram": "string",
    "lexicographic": "string", "pattern": "string",
    # geometry
    "point": "geometry", "polygon": "geometry", "angle": "geometry",
    "coordinate": "geometry", "convex": "geometry",
}

_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_MATH = re.compile(r"\$+[^$]+\$+")
_NON_ALPHA = re.compile(r"[^a-z0-9+\- ]+")
_WS = re.compile(r"\s+")


def normalize_tag(tag: str) -> str:
    tag = tag.strip().lower()
    return TAG_SYNONYMS.get(tag, tag.replace(" ", "-"))


def normalize_tags(tags: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for t in tags:
        nt = normalize_tag(t)
        if nt and nt not in seen:
            seen.append(nt)
    return seen


def graph_tags(tags: Iterable[str]) -> list[str]:
    """Tags used for the structural adjacency graph (generic ones removed)."""
    return [t for t in normalize_tags(tags) if t not in GENERIC_TAGS_FOR_GRAPH]


def clean_text(raw: str) -> str:
    """Lowercase, strip code/math, collapse whitespace."""
    if not raw:
        return ""
    text = _CODE_FENCE.sub(" ", raw)
    text = _INLINE_MATH.sub(" ", text)
    text = text.lower()
    text = _NON_ALPHA.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    return text


def inject_algorithmic_tokens(text: str) -> str:
    """Append canonical algorithmic tokens discovered in the story text."""
    extra: list[str] = []
    for keyword, token in ALGO_KEYWORD_MAP.items():
        if keyword in text and token not in extra:
            extra.append(token)
    return text + " " + " ".join(extra)


def build_corpus(text: str, tags: list[str]) -> str:
    """Build a tag-boosted, keyword-injected document for LSA.

    The tags (the reliable algorithmic signal) are repeated ``tag_boost`` times
    so they dominate term frequencies, defeating story-noun clustering.
    """
    tags = normalize_tags(tags)
    cleaned = inject_algorithmic_tokens(clean_text(text))
    tag_part = " ".join(tags * settings.tag_boost)
    return f"{tag_part} {cleaned}".strip()
