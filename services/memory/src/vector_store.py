from typing import Dict, List, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer


class VectorStore:
    """Vector store for agent memories using Qdrant"""

    def __init__(self, client: QdrantClient, model_name: str = "all-MiniLM-L6-v2"):
        self.client = client
        self.model = SentenceTransformer(model_name)
        self.collection_name = "agent_memories"
        self.vector_size = 384  # all-MiniLM-L6-v2 dimension
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    async def store(
        self,
        memory_id: str,
        content: str,
        agent_did: str,
        conversation_id: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Store memory with vector embedding"""
        if not memory_id:
            raise ValueError("memory_id is required")
        if not content:
            raise ValueError("content is required")
        if not agent_did:
            raise ValueError("agent_did is required")
        if not conversation_id:
            raise ValueError("conversation_id is required")

        embedding = self.model.encode(content).tolist()

        payload = {
            "memory_id": memory_id,
            "content": content,
            "agent_did": agent_did,
            "conversation_id": conversation_id,
        }
        if metadata:
            payload.update(metadata)

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload,
        )

        self.client.upsert(collection_name=self.collection_name, points=[point])

    async def search(
        self,
        query: str,
        agent_did: str,
        conversation_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search memories by semantic similarity"""
        if not query:
            raise ValueError("query is required")
        if not agent_did:
            raise ValueError("agent_did is required")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        query_vector = self.model.encode(query).tolist()

        # Build filter
        must_conditions = [FieldCondition(key="agent_did", match=MatchValue(value=agent_did))]

        if conversation_id:
            must_conditions.append(
                FieldCondition(key="conversation_id", match=MatchValue(value=conversation_id))
            )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=must_conditions),
            limit=limit,
        )

        return [
            {
                "memory_id": hit.payload["memory_id"],
                "content": hit.payload["content"],
                "score": hit.score,
                "metadata": {
                    k: v
                    for k, v in hit.payload.items()
                    if k not in ["memory_id", "content", "agent_did", "conversation_id"]
                },
            }
            for hit in results
        ]
