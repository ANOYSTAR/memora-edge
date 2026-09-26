"""
Sync Agent — Manages memory synchronization between local and cloud.
Queues memories while offline, syncs approved ones when online.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sqlalchemy import select, update

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import Memory, SyncQueueItem, async_session, init_db
from config import (
    QDRANT_HOST, QDRANT_PORT,
    QDRANT_COLLECTION_LOCAL, QDRANT_COLLECTION_CLOUD,
    EMBEDDING_DIM, SYNC_BATCH_SIZE, app_state
)


class SyncAgent:
    """Manages the synchronization lifecycle between local and cloud collections."""

    def __init__(self):
        self._qdrant: Optional[QdrantClient] = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        self._qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Ensure cloud collection exists
        collections = [c.name for c in self._qdrant.get_collections().collections]
        if QDRANT_COLLECTION_CLOUD not in collections:
            self._qdrant.create_collection(
                collection_name=QDRANT_COLLECTION_CLOUD,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
        await init_db()
        self._initialized = True

    async def queue_for_sync(self, memory_id: str) -> Dict[str, Any]:
        """Add a memory to the sync queue."""
        await self.initialize()
        
        async with async_session() as session:
            # Check if memory exists and is sync_allowed
            result = await session.execute(select(Memory).where(Memory.id == memory_id))
            memory = result.scalar_one_or_none()
            
            if not memory:
                return {"error": "Memory not found", "status": "failed"}
            
            if memory.privacy == "local_only":
                return {"error": "Memory is marked local_only", "status": "blocked"}
            
            if memory.synced:
                return {"error": "Memory already synced", "status": "already_synced"}
            
            # Check if already in queue
            existing = await session.execute(
                select(SyncQueueItem).where(
                    SyncQueueItem.memory_id == memory_id,
                    SyncQueueItem.status.in_(["pending", "syncing"])
                )
            )
            if existing.scalar_one_or_none():
                return {"status": "already_queued", "memory_id": memory_id}
            
            # Add to queue
            queue_item = SyncQueueItem(
                id=str(uuid.uuid4()),
                memory_id=memory_id,
                status="pending",
            )
            session.add(queue_item)
            await session.commit()
            
            return {
                "status": "queued",
                "memory_id": memory_id,
                "queue_id": queue_item.id,
            }

    async def sync_pending(self) -> Dict[str, Any]:
        """Sync all pending memories to the cloud collection."""
        await self.initialize()
        
        if not app_state.is_online:
            return {
                "status": "offline",
                "message": "Cannot sync while offline",
                "synced_count": 0,
            }
        
        synced = []
        failed = []
        
        async with async_session() as session:
            # Get pending items
            result = await session.execute(
                select(SyncQueueItem)
                .where(SyncQueueItem.status == "pending")
                .limit(SYNC_BATCH_SIZE)
            )
            pending_items = result.scalars().all()
            
            for item in pending_items:
                try:
                    # Get the memory
                    mem_result = await session.execute(
                        select(Memory).where(Memory.id == item.memory_id)
                    )
                    memory = mem_result.scalar_one_or_none()
                    
                    if not memory or memory.privacy == "local_only":
                        item.status = "failed"
                        item.error_message = "Memory not found or local_only"
                        failed.append(item.memory_id)
                        continue
                    
                    # Get vector from local collection
                    try:
                        points = self._qdrant.retrieve(
                            collection_name=QDRANT_COLLECTION_LOCAL,
                            ids=[memory.id],
                            with_vectors=True,
                            with_payload=True,
                        )
                    except Exception:
                        points = []
                    
                    if not points:
                        item.status = "failed"
                        item.error_message = "Vector not found in local collection"
                        failed.append(item.memory_id)
                        continue
                    
                    point = points[0]
                    
                    # Copy to cloud collection
                    self._qdrant.upsert(
                        collection_name=QDRANT_COLLECTION_CLOUD,
                        points=[
                            PointStruct(
                                id=point.id,
                                vector=point.vector,
                                payload={
                                    **point.payload,
                                    "synced": True,
                                    "sync_timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                        ]
                    )
                    
                    # Update sync status
                    memory.synced = True
                    memory.sync_timestamp = datetime.utcnow()
                    item.status = "synced"
                    item.synced_at = datetime.utcnow()
                    
                    # Update local Qdrant payload
                    self._qdrant.set_payload(
                        collection_name=QDRANT_COLLECTION_LOCAL,
                        payload={"synced": True},
                        points=[memory.id],
                    )
                    
                    synced.append(memory.id)
                    
                except Exception as e:
                    item.status = "failed"
                    item.error_message = str(e)
                    item.retry_count += 1
                    failed.append(item.memory_id)
            
            await session.commit()
        
        return {
            "status": "completed",
            "synced_count": len(synced),
            "failed_count": len(failed),
            "synced_ids": synced,
            "failed_ids": failed,
        }

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        await self.initialize()
        
        async with async_session() as session:
            all_result = await session.execute(select(SyncQueueItem))
            items = all_result.scalars().all()
            
            pending = [i for i in items if i.status == "pending"]
            synced = [i for i in items if i.status == "synced"]
            failed = [i for i in items if i.status == "failed"]
            
            # Get memory counts
            mem_result = await session.execute(select(Memory))
            memories = mem_result.scalars().all()
            
            local_only = [m for m in memories if m.privacy == "local_only"]
            synced_memories = [m for m in memories if m.synced]
            pending_memories = [m for m in memories if not m.synced and m.privacy == "sync_allowed"]
            
            return {
                "is_online": app_state.is_online,
                "queue": {
                    "pending": len(pending),
                    "synced": len(synced),
                    "failed": len(failed),
                    "total": len(items),
                },
                "memories": {
                    "total": len(memories),
                    "local_only": len(local_only),
                    "synced": len(synced_memories),
                    "pending_sync": len(pending_memories),
                },
                "pending_items": [
                    {
                        "queue_id": p.id,
                        "memory_id": p.memory_id,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in pending[:20]
                ],
                "recent_synced": [
                    {
                        "queue_id": s.id,
                        "memory_id": s.memory_id,
                        "synced_at": s.synced_at.isoformat() if s.synced_at else None,
                    }
                    for s in sorted(synced, key=lambda x: x.synced_at or x.created_at, reverse=True)[:10]
                ],
            }

    async def auto_queue_all(self) -> Dict[str, Any]:
        """Automatically queue all sync_allowed, unsynced memories."""
        await self.initialize()
        
        queued = []
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(
                    Memory.synced == False,
                    Memory.privacy == "sync_allowed",
                )
            )
            memories = result.scalars().all()
            
            for memory in memories:
                # Check if already queued
                existing = await session.execute(
                    select(SyncQueueItem).where(
                        SyncQueueItem.memory_id == memory.id,
                        SyncQueueItem.status.in_(["pending", "syncing"])
                    )
                )
                if existing.scalar_one_or_none():
                    continue
                
                queue_item = SyncQueueItem(
                    id=str(uuid.uuid4()),
                    memory_id=memory.id,
                    status="pending",
                )
                session.add(queue_item)
                queued.append(memory.id)
            
            await session.commit()
        
        return {
            "queued_count": len(queued),
            "queued_ids": queued,
        }
