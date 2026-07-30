"""Seed the vector DB with a few sample documents.

Run:  uv run python -m scripts.seed_knowledge
"""
from __future__ import annotations

from app.schemas import Document
from app.vectorstore import get_vector_store

SAMPLE_DOCS = [
    Document(
        text="The AI Agent Service uses FastAPI and OpenAI function calling.",
        metadata={"topic": "architecture"},
    ),
    Document(
        text="Qdrant stores embeddings; fastembed generates them locally with BGE.",
        metadata={"topic": "vector-db"},
    ),
    Document(
        text="Instructor forces the LLM to return output validated by a Pydantic schema.",
        metadata={"topic": "structured-output"},
    ),
    Document(
        text="The office is closed on public holidays and the last Friday of each month.",
        metadata={"topic": "policy"},
    ),
    Document(
        text="Support requests should be triaged within 4 business hours.",
        metadata={"topic": "policy"},
    ),
]


def main() -> None:
    store = get_vector_store()
    ids = store.add(SAMPLE_DOCS)
    print(f"Seeded {len(ids)} documents. Total in collection: {store.count()}")


if __name__ == "__main__":
    main()
