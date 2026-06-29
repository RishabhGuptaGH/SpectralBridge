"""Resilient HTTP client: exponential backoff + jitter.

Defends against the *API Rate Limits* reality check. LeetCode's GraphQL endpoint
is aggressive against scrapers, so every request goes through a bounded retry
loop with exponential backoff and jitter, plus a polite base delay between calls.
"""
from __future__ import annotations

import asyncio
import random
import time

import httpx

from ..config import settings


class RateLimitedClient:
    def __init__(self, base_delay: float = 1.0, max_retries: int = 6):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self._last_request = 0.0

    async def _throttle(self):
        # enforce a polite minimum gap between successive requests
        gap = time.monotonic() - self._last_request
        if gap < self.base_delay:
            await asyncio.sleep(self.base_delay - gap)
        self._last_request = time.monotonic()

    async def get_json(self, client: httpx.AsyncClient, url: str, **kwargs) -> dict:
        return await self._request(client, "GET", url, **kwargs)

    async def post_json(self, client: httpx.AsyncClient, url: str, **kwargs) -> dict:
        return await self._request(client, "POST", url, **kwargs)

    async def _request(self, client: httpx.AsyncClient, method: str, url: str, **kwargs) -> dict:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            await self._throttle()
            try:
                resp = await client.request(method, url, **kwargs)
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                await self._backoff(attempt)
                continue

            if resp.status_code == 429 or resp.status_code >= 500:
                last_exc = RuntimeError(f"HTTP {resp.status_code} from {url}")
                await self._backoff(attempt)
                continue
            resp.raise_for_status()
            return resp.json()

        raise RuntimeError(f"Request to {url} failed after {self.max_retries} retries") from last_exc

    async def _backoff(self, attempt: int):
        # exponential backoff with full jitter
        delay = min(30.0, (2 ** attempt)) + random.uniform(0, 1.0)
        await asyncio.sleep(delay)
