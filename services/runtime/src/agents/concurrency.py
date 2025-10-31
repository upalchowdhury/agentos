"""In-memory concurrency limiter for per-agent invocation caps."""

import asyncio
from typing import Dict


class _AgentLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = max(1, limit)
        self.current = 0
        self._lock = asyncio.Lock()

    async def try_acquire(self, limit: int) -> bool:
        """Attempt to reserve a concurrent slot."""
        async with self._lock:
            if limit != self.limit:
                self.limit = max(1, limit)
                if self.current > self.limit:
                    self.current = self.limit
            if self.current >= self.limit:
                return False
            self.current += 1
            return True

    async def release(self) -> None:
        async with self._lock:
            if self.current > 0:
                self.current -= 1

    async def get_usage(self) -> int:
        async with self._lock:
            return self.current


class ConcurrencyManager:
    def __init__(self) -> None:
        self._limiters: Dict[str, _AgentLimiter] = {}
        self._registry_lock = asyncio.Lock()

    async def _get_limiter(self, agent_id: str, limit: int) -> _AgentLimiter:
        async with self._registry_lock:
            limiter = self._limiters.get(agent_id)
            if not limiter:
                limiter = _AgentLimiter(limit)
                self._limiters[agent_id] = limiter
        return limiter

    async def try_acquire(self, agent_id: str, limit: int) -> bool:
        limiter = await self._get_limiter(agent_id, limit)
        return await limiter.try_acquire(limit)

    async def release(self, agent_id: str) -> None:
        limiter = self._limiters.get(agent_id)
        if limiter:
            await limiter.release()

    async def current_usage(self, agent_id: str) -> int:
        limiter = self._limiters.get(agent_id)
        if not limiter:
            return 0
        return await limiter.get_usage()


concurrency_manager = ConcurrencyManager()
