import os
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from qdrant_client import QdrantClient
import asyncpg

from .vector_store import VectorStore
from .context_manager import ContextManager
from .isolation import TenantIsolation

# Global state
db_pool: Optional[asyncpg.Pool] = None
vector_store: Optional[VectorStore] = None
context_manager: Optional[ContextManager] = None
tenant_isolation: Optional[TenantIsolation] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, vector_store, context_manager, tenant_isolation

    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agentos"),
        min_size=10,
        max_size=20,
        command_timeout=5,
    )

    # Initialize Qdrant client
    qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

    # Initialize services
    vector_store = VectorStore(qdrant)
    context_manager = ContextManager(db_pool, vector_store)
    tenant_isolation = TenantIsolation(db_pool)

    yield

    # Cleanup
    if db_pool:
        await db_pool.close()


app = FastAPI(lifespan=lifespan, title="Agent Memory Service", version="0.1.0")
FastAPIInstrumentor.instrument_app(app)


@app.post("/api/v1/memories")
async def store_memory(
    agent_did: str,
    conversation_id: str,
    content: str,
    metadata: Optional[dict] = None,
):
    """Store a memory with vector embedding"""
    if not agent_did or not conversation_id or not content:
        raise HTTPException(400, "agent_did, conversation_id, and content are required")

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("store_memory") as span:
        span.set_attributes(
            {
                "agent.did": agent_did,
                "conversation.id": conversation_id,
            }
        )

        try:
            # Check write access
            if not await tenant_isolation.can_write(agent_did, conversation_id):
                raise HTTPException(403, "Access denied")

            memory_id = await context_manager.store(
                agent_did=agent_did,
                conversation_id=conversation_id,
                content=content,
                metadata=metadata or {},
            )

            return {"memory_id": memory_id}
        except ValueError as e:
            span.record_exception(e)
            raise HTTPException(400, str(e))
        except Exception as e:
            span.record_exception(e)
            raise HTTPException(500, str(e))


@app.get("/api/v1/memories/search")
async def search_memories(
    agent_did: str,
    conversation_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 10,
):
    """Search memories with vector similarity"""
    if not agent_did:
        raise HTTPException(400, "agent_did is required")

    try:
        # Check read access
        if not await tenant_isolation.can_read(agent_did, conversation_id):
            raise HTTPException(403, "Access denied")

        results = await context_manager.search(
            agent_did=agent_did,
            conversation_id=conversation_id,
            query=query,
            limit=limit,
        )

        return {"results": results}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/v1/context/{conversation_id}")
async def get_context(
    conversation_id: str,
    agent_did: str,
    limit: int = 50,
):
    """Get recent context for a conversation"""
    if not conversation_id or not agent_did:
        raise HTTPException(400, "conversation_id and agent_did are required")

    try:
        if not await tenant_isolation.can_read(agent_did, conversation_id):
            raise HTTPException(403, "Access denied")

        context = await context_manager.get_recent_context(
            agent_did=agent_did,
            conversation_id=conversation_id,
            limit=limit,
        )

        return {"context": context}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/v1/interactions")
async def store_interaction(
    caller_did: str,
    target_did: str,
    conversation_id: str,
    request: dict,
    response: dict,
):
    """Store agent interaction for audit/replay"""
    if not caller_did or not target_did or not conversation_id:
        raise HTTPException(400, "caller_did, target_did, and conversation_id are required")

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO interactions 
            (caller_did, target_did, conversation_id, request, response, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            """,
            caller_did,
            target_did,
            conversation_id,
            json.dumps(request),
            json.dumps(response),
        )

    return {"status": "stored"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
