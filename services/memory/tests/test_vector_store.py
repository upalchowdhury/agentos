import pytest
from qdrant_client import QdrantClient
from src.vector_store import VectorStore


@pytest.fixture
def qdrant_client():
    """Fixture for Qdrant client"""
    client = QdrantClient(":memory:")
    return client


@pytest.fixture
def vector_store(qdrant_client):
    """Fixture for VectorStore"""
    return VectorStore(qdrant_client)


@pytest.mark.asyncio
async def test_store_memory(vector_store):
    """Test storing a memory"""
    await vector_store.store(
        memory_id="test-123",
        content="Test memory content",
        agent_did="did:agent:test",
        conversation_id="conv-123",
        metadata={"topic": "testing"},
    )
    # If no exception, test passes


@pytest.mark.asyncio
async def test_store_memory_validation(vector_store):
    """Test validation errors"""
    with pytest.raises(ValueError, match="memory_id is required"):
        await vector_store.store(
            memory_id="",
            content="Test",
            agent_did="did:agent:test",
            conversation_id="conv-123",
        )

    with pytest.raises(ValueError, match="content is required"):
        await vector_store.store(
            memory_id="test-123",
            content="",
            agent_did="did:agent:test",
            conversation_id="conv-123",
        )


@pytest.mark.asyncio
async def test_search_memories(vector_store):
    """Test semantic search"""
    # Store test memories
    await vector_store.store(
        memory_id="mem-1",
        content="The user wants to know about pricing",
        agent_did="did:agent:test",
        conversation_id="conv-123",
    )

    await vector_store.store(
        memory_id="mem-2",
        content="The user asked about features",
        agent_did="did:agent:test",
        conversation_id="conv-123",
    )

    # Search
    results = await vector_store.search(
        query="pricing information",
        agent_did="did:agent:test",
        conversation_id="conv-123",
        limit=10,
    )

    assert len(results) > 0
    assert results[0]["memory_id"] in ["mem-1", "mem-2"]
    assert "score" in results[0]


@pytest.mark.asyncio
async def test_search_validation(vector_store):
    """Test search validation"""
    with pytest.raises(ValueError, match="query is required"):
        await vector_store.search(
            query="",
            agent_did="did:agent:test",
        )

    with pytest.raises(ValueError, match="limit must be between"):
        await vector_store.search(
            query="test",
            agent_did="did:agent:test",
            limit=0,
        )
