"""
Memory Agent — Stores memories and embeddings.
Handles the full pipeline: text → embedding → Qdrant + SQLite.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import Memory, async_session, init_db
from config import (
    QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_LOCAL,
    EMBEDDING_MODEL, EMBEDDING_DIM
)


class MemoryAgent:
    """Stores memories with embeddings into Qdrant Edge and metadata into SQLite."""

    def __init__(self):
        self._encoder: Optional[SentenceTransformer] = None
        self._qdrant: Optional[QdrantClient] = None
        self._initialized = False

    async def initialize(self):
        """Lazy initialization of heavy resources."""
        if self._initialized:
            return
        self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        self._qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Create local collection if it doesn't exist
        collections = [c.name for c in self._qdrant.get_collections().collections]
        if QDRANT_COLLECTION_LOCAL not in collections:
            self._qdrant.create_collection(
                collection_name=QDRANT_COLLECTION_LOCAL,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
        await init_db()
        self._initialized = True

    def encode(self, text: str) -> list:
        """Generate embedding vector for text."""
        return self._encoder.encode(text).tolist()

    async def store_memory(
        self,
        text: str,
        source: str = "chat",
        importance: str = "medium",
        importance_score: float = 0.5,
        privacy: str = "sync_allowed",
        category: str = "personal",
        memory_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store a new memory:
        1. Generate embedding
        2. Insert vector into Qdrant Edge
        3. Insert metadata into SQLite
        """
        await self.initialize()
        
        mid = memory_id or str(uuid.uuid4())
        embedding = self.encode(text)
        now = datetime.utcnow()

        # Store in Qdrant
        self._qdrant.upsert(
            collection_name=QDRANT_COLLECTION_LOCAL,
            points=[
                PointStruct(
                    id=mid,
                    vector=embedding,
                    payload={
                        "text": text,
                        "source": source,
                        "importance": importance,
                        "importance_score": importance_score,
                        "privacy": privacy,
                        "category": category,
                        "timestamp": now.isoformat(),
                        "synced": False,
                    }
                )
            ]
        )

        # Store metadata in SQLite
        memory = Memory(
            id=mid,
            text=text,
            timestamp=now,
            source=source,
            importance=importance,
            importance_score=importance_score,
            privacy=privacy,
            category=category,
            synced=False,
            embedding_stored=True,
        )
        async with async_session() as session:
            session.add(memory)
            await session.commit()

        return {
            "id": mid,
            "text": text,
            "source": source,
            "importance": importance,
            "importance_score": importance_score,
            "privacy": privacy,
            "category": category,
            "timestamp": now.isoformat(),
            "synced": False,
        }

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single memory by ID."""
        async with async_session() as session:
            result = await session.execute(select(Memory).where(Memory.id == memory_id))
            memory = result.scalar_one_or_none()
            if memory:
                return {
                    "id": memory.id,
                    "text": memory.text,
                    "source": memory.source,
                    "importance": memory.importance,
                    "importance_score": memory.importance_score,
                    "privacy": memory.privacy,
                    "category": memory.category,
                    "timestamp": memory.timestamp.isoformat(),
                    "synced": memory.synced,
                }
        return None

    async def get_all_memories(
        self, limit: int = 100, offset: int = 0
    ) -> list:
        """Get all memories with pagination."""
        async with async_session() as session:
            result = await session.execute(
                select(Memory)
                .order_by(Memory.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            memories = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "text": m.text,
                    "source": m.source,
                    "importance": m.importance,
                    "importance_score": m.importance_score,
                    "privacy": m.privacy,
                    "category": m.category,
                    "timestamp": m.timestamp.isoformat(),
                    "synced": m.synced,
                }
                for m in memories
            ]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from both Qdrant and SQLite."""
        await self.initialize()
        try:
            self._qdrant.delete(
                collection_name=QDRANT_COLLECTION_LOCAL,
                points_selector=[memory_id],
            )
        except Exception:
            pass
        
        async with async_session() as session:
            result = await session.execute(select(Memory).where(Memory.id == memory_id))
            memory = result.scalar_one_or_none()
            if memory:
                await session.delete(memory)
                await session.commit()
                return True
        return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        async with async_session() as session:
            all_result = await session.execute(select(Memory))
            all_memories = all_result.scalars().all()
            
            total = len(all_memories)
            synced = sum(1 for m in all_memories if m.synced)
            local_only = sum(1 for m in all_memories if m.privacy == "local_only")
            pending = sum(1 for m in all_memories if not m.synced and m.privacy == "sync_allowed")
            
            categories = {}
            for m in all_memories:
                categories[m.category] = categories.get(m.category, 0) + 1
            
            importances = {}
            for m in all_memories:
                importances[m.importance] = importances.get(m.importance, 0) + 1

            return {
                "total": total,
                "synced": synced,
                "local_only": local_only,
                "pending_sync": pending,
                "categories": categories,
                "importances": importances,
            }
