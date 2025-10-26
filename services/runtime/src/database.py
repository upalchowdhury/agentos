import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

import asyncpg

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None
        self.dsn = settings.database_url
    
    async def connect(self) -> None:
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self) -> None:
        if self.pool:
            try:
                await self.pool.close()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
                raise
    
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        conn = await self.pool.acquire()
        try:
            async with conn.transaction():
                yield conn
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise
        finally:
            await self.pool.release(conn)
    
    async def execute(self, query: str, *args: Any) -> str:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *args)
                return result
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise
    
    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return rows
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raise
    
    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return row
        except Exception as e:
            logger.error(f"Fetchrow error: {e}")
            raise


db = Database()
