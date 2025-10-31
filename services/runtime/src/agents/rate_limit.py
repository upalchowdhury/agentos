"""Token-bucket rate limiting for Model B external agents."""

import asyncio
import time
from typing import Dict, Tuple


class _TokenBucket:
    def __init__(self, rps: float, burst: int) -> None:
        self.rps = max(0.1, float(rps))
        self.capacity = max(1, int(burst))
        self.tokens = float(self.capacity)
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def try_consume(self, rps: float, burst: int) -> bool:
        async with self._lock:
            if rps != self.rps or burst != self.capacity:
                self.rps = max(0.1, float(rps))
                self.capacity = max(1, int(burst))
                self.tokens = min(self.tokens, float(self.capacity))

            now = time.monotonic()
            elapsed = now - self.updated_at
            self.updated_at = now

            self.tokens = min(
                float(self.capacity),
                self.tokens + elapsed * self.rps,
            )

            if self.tokens < 1.0:
                return False

            self.tokens -= 1.0
            return True


class RateLimitManager:
    def __init__(self) -> None:
        self._buckets: Dict[str, _TokenBucket] = {}
        self._lock = asyncio.Lock()

    async def _get_bucket(self, agent_id: str, rps: float, burst: int) -> _TokenBucket:
        async with self._lock:
            bucket = self._buckets.get(agent_id)
            if bucket is None:
                bucket = _TokenBucket(rps, burst)
                self._buckets[agent_id] = bucket
        return bucket

    async def try_acquire(self, agent_id: str, rps: float, burst: int) -> bool:
        bucket = await self._get_bucket(agent_id, rps, burst)
        return await bucket.try_consume(rps, burst)


rate_limit_manager = RateLimitManager()
