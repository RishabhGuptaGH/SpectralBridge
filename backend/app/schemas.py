from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    url: Optional[str] = Field(default=None, description="Codeforces or LeetCode problem URL")
    problem_id: Optional[str] = Field(default=None, description="Canonical id e.g. cf:1200/A")
    top_k: Optional[int] = Field(default=3, ge=1, le=10)


class RecommendationOut(BaseModel):
    id: str
    platform: str
    title: str
    url: str
    tags: list[str]
    difficulty: str
    rating: Optional[float]
    similarity: float
    reason: str


class RecommendResponse(BaseModel):
    target: dict
    recommendations: list[RecommendationOut]
    note: Optional[str] = None


class ProblemOut(BaseModel):
    id: str
    platform: str
    title: str
    url: str
    tags: list[str]
    difficulty: str
    rating: Optional[float]


class StatsOut(BaseModel):
    total: int
    codeforces: int
    leetcode: int
    lsa_dimensions: int
    fused_dimensions: int
    rating_min: Optional[float]
    rating_max: Optional[float]
    tag_count: int
