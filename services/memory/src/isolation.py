from typing import Optional
import asyncpg


class TenantIsolation:
    """Enforces tenant isolation for memory access"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def can_read(self, agent_did: str, conversation_id: Optional[str] = None) -> bool:
        """Check if agent has read access"""
        if not agent_did:
            return False

        if not conversation_id:
            return True  # Agent can always read their own memories

        # Check if agent has explicit access to the conversation
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM tenant_access
                    WHERE agent_did = $1
                    AND resource_type = 'conversation'
                    AND resource_id = $2
                    AND permission IN ('read', 'write', 'admin')
                )
                """,
                agent_did,
                conversation_id,
            )

            if result:
                return True

            # Check if agent is participant in the conversation
            result = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM memories
                    WHERE agent_did = $1
                    AND conversation_id = $2
                )
                """,
                agent_did,
                conversation_id,
            )

            return bool(result)

    async def can_write(self, agent_did: str, conversation_id: str) -> bool:
        """Check if agent has write access"""
        if not agent_did or not conversation_id:
            return False

        # Check if agent has explicit write access
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM tenant_access
                    WHERE agent_did = $1
                    AND resource_type = 'conversation'
                    AND resource_id = $2
                    AND permission IN ('write', 'admin')
                )
                """,
                agent_did,
                conversation_id,
            )

            if result:
                return True

            # Agent can always write to conversations they're part of
            return True

    async def grant_access(
        self,
        agent_did: str,
        resource_type: str,
        resource_id: str,
        permission: str,
    ) -> None:
        """Grant access to a resource"""
        if permission not in ["read", "write", "admin"]:
            raise ValueError("permission must be read, write, or admin")

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tenant_access (agent_did, resource_type, resource_id, permission)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (agent_did, resource_type, resource_id, permission) DO NOTHING
                """,
                agent_did,
                resource_type,
                resource_id,
                permission,
            )

    async def revoke_access(
        self,
        agent_did: str,
        resource_type: str,
        resource_id: str,
        permission: Optional[str] = None,
    ) -> None:
        """Revoke access to a resource"""
        async with self.db_pool.acquire() as conn:
            if permission:
                await conn.execute(
                    """
                    DELETE FROM tenant_access
                    WHERE agent_did = $1
                    AND resource_type = $2
                    AND resource_id = $3
                    AND permission = $4
                    """,
                    agent_did,
                    resource_type,
                    resource_id,
                    permission,
                )
            else:
                await conn.execute(
                    """
                    DELETE FROM tenant_access
                    WHERE agent_did = $1
                    AND resource_type = $2
                    AND resource_id = $3
                    """,
                    agent_did,
                    resource_type,
                    resource_id,
                )
