from typing import Dict, List, Optional
import uuid
import asyncpg

from .vector_store import VectorStore


class ContextManager:
    """Manages conversation context and memory storage"""

    def __init__(self, db_pool: asyncpg.Pool, vector_store: VectorStore):
        self.db_pool = db_pool
        self.vector_store = vector_store

    async def store(
        self,
        agent_did: str,
        conversation_id: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store a memory with vector embedding"""
        if not agent_did:
            raise ValueError("agent_did is required")
        if not conversation_id:
            raise ValueError("conversation_id is required")
        if not content:
            raise ValueError("content is required")

        memory_id = str(uuid.uuid4())

        # Store in relational database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO memories (id, agent_did, conversation_id, content, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                """,
                memory_id,
                agent_did,
                conversation_id,
                content,
                metadata or {},
            )

        # Store vector embedding
        await self.vector_store.store(
            memory_id=memory_id,
            content=content,
            agent_did=agent_did,
            conversation_id=conversation_id,
            metadata=metadata,
        )

        return memory_id

    async def search(
        self,
        agent_did: str,
        conversation_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search memories by semantic similarity"""
        if not agent_did:
            raise ValueError("agent_did is required")

        if query:
            # Vector search
            return await self.vector_store.search(
                query=query,
                agent_did=agent_did,
                conversation_id=conversation_id,
                limit=limit,
            )
        else:
            # Return recent memories
            return await self.get_recent_context(
                agent_did=agent_did,
                conversation_id=conversation_id,
                limit=limit,
            )

    async def get_recent_context(
        self,
        agent_did: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get recent context for a conversation"""
        if not conversation_id and not agent_did:
            raise ValueError("either agent_did or conversation_id is required")

        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")

        query = """
            SELECT id, agent_did, conversation_id, content, metadata, created_at
            FROM memories
            WHERE 1=1
        """
        params: List = []
        param_count = 1

        if agent_did:
            query += f" AND agent_did = ${param_count}"
            params.append(agent_did)
            param_count += 1

        if conversation_id:
            query += f" AND conversation_id = ${param_count}"
            params.append(conversation_id)
            param_count += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_count}"
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            {
                "memory_id": str(row["id"]),
                "agent_did": row["agent_did"],
                "conversation_id": row["conversation_id"],
                "content": row["content"],
                "metadata": row["metadata"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ]
