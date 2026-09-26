"""
Retrieval Agent — Semantic search using Qdrant Edge.
Performs vector similarity search and hybrid filtering.
"""
from typing import Optional, Dict, Any, List

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchParams
from sentence_transformers import SentenceTransformer

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_LOCAL,
    QDRANT_COLLECTION_CLOUD, EMBEDDING_MODEL, EMBEDDING_DIM
)


class RetrievalAgent:
    """Performs semantic search over local and cloud memory collections."""

    def __init__(self):
        self._encoder: Optional[SentenceTransformer] = None
        self._qdrant: Optional[QdrantClient] = None
        self._initialized = False

    def initialize(self):
        """Lazy initialization."""
        if self._initialized:
            return
        self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        self._qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self._initialized = True

    def encode(self, text: str) -> list:
        """Generate embedding for search query."""
        return self._encoder.encode(text).tolist()

    def search(
        self,
        query: str,
        collection: str = QDRANT_COLLECTION_LOCAL,
        limit: int = 10,
        category: Optional[str] = None,
        importance: Optional[str] = None,
        privacy: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with optional metadata filters.
        Returns results sorted by similarity score.
        """
        self.initialize()
        query_vector = self.encode(query)

        # Build filter conditions
        conditions = []
        if category:
            conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category))
            )
        if importance:
            conditions.append(
                FieldCondition(key="importance", match=MatchValue(value=importance))
            )
        if privacy:
            conditions.append(
                FieldCondition(key="privacy", match=MatchValue(value=privacy))
            )

        search_filter = Filter(must=conditions) if conditions else None

        try:
            results = self._qdrant.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=min_score,
            )
        except Exception:
            return []

        return [
            {
                "id": str(hit.id),
                "score": round(hit.score, 4),
                "text": hit.payload.get("text", ""),
                "source": hit.payload.get("source", "unknown"),
                "importance": hit.payload.get("importance", "medium"),
                "importance_score": hit.payload.get("importance_score", 0.5),
                "privacy": hit.payload.get("privacy", "sync_allowed"),
                "category": hit.payload.get("category", "personal"),
                "timestamp": hit.payload.get("timestamp", ""),
                "synced": hit.payload.get("synced", False),
            }
            for hit in results
        ]

    def search_local(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search only local memory collection."""
        return self.search(query, collection=QDRANT_COLLECTION_LOCAL, **kwargs)

    def search_cloud(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search only cloud memory collection."""
        return self.search(query, collection=QDRANT_COLLECTION_CLOUD, **kwargs)

    def search_all(self, query: str, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """Search both local and cloud, return combined results."""
        local = self.search_local(query, **kwargs)
        cloud = self.search_cloud(query, **kwargs)
        
        # Merge and deduplicate by ID, keeping highest score
        seen = {}
        for item in local + cloud:
            mid = item["id"]
            if mid not in seen or item["score"] > seen[mid]["score"]:
                seen[mid] = item
        
        combined = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
        
        return {
            "local": local,
            "cloud": cloud,
            "combined": combined,
        }

    def get_similar(self, memory_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find memories similar to an existing memory."""
        self.initialize()
        try:
            points = self._qdrant.retrieve(
                collection_name=QDRANT_COLLECTION_LOCAL,
                ids=[memory_id],
                with_vectors=True,
            )
            if not points:
                return []
            
            vector = points[0].vector
            results = self._qdrant.search(
                collection_name=QDRANT_COLLECTION_LOCAL,
                query_vector=vector,
                limit=limit + 1,  # +1 because the query itself will match
            )
            
            return [
                {
                    "id": str(hit.id),
                    "score": round(hit.score, 4),
                    "text": hit.payload.get("text", ""),
                    "category": hit.payload.get("category", "personal"),
                    "importance": hit.payload.get("importance", "medium"),
                }
                for hit in results
                if str(hit.id) != memory_id
            ][:limit]
        except Exception:
            return []
