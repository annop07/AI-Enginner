"""Vector store wrapper around Qdrant.

Uses fastembed (local, no API key) for embeddings so the similarity-search
feature works out of the box. Qdrant runs in local file mode by default;
set QDRANT_LOCATION=http://localhost:6333 to talk to a real server instead.
"""
from __future__ import annotations

import atexit
import uuid
from functools import lru_cache

from qdrant_client import QdrantClient, models

from app.config import get_settings
from app.schemas import Document, SearchHit


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.collection = settings.qdrant_collection

        location = settings.qdrant_location
        if location.startswith("http"):
            self.client = QdrantClient(url=location)
        elif location == ":memory:":
            # Ephemeral, in-process — handy for tests.
            self.client = QdrantClient(location=":memory:")
        else:
            # Local, embedded, persistent mode — zero infrastructure.
            self.client = QdrantClient(path=location)

        # fastembed is bundled with qdrant-client[fastembed]; this makes
        # client.add()/client.query() embed text locally for us.
        self.client.set_model(settings.embedding_model)

        # Local file mode holds a lock; close it while the interpreter is
        # still alive to avoid a noisy shutdown error.
        atexit.register(self._safe_close)

    def _safe_close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass

    def add(self, documents: list[Document]) -> list[str]:
        ids = [doc.id or uuid.uuid4().hex for doc in documents]
        self.client.add(
            collection_name=self.collection,
            documents=[doc.text for doc in documents],
            metadata=[doc.metadata for doc in documents],
            ids=ids,
        )
        return ids

    def search(self, query: str, top_k: int = 3) -> list[SearchHit]:
        results = self.client.query(
            collection_name=self.collection,
            query_text=query,
            limit=top_k,
        )
        return [
            SearchHit(
                text=r.document or r.metadata.get("document", ""),
                score=round(r.score, 4),
                metadata={k: v for k, v in r.metadata.items() if k != "document"},
            )
            for r in results
        ]

    def count(self) -> int:
        try:
            return self.client.count(self.collection).count
        except Exception:
            return 0


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()
