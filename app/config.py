"""Application configuration loaded from environment variables.

Uses pydantic-settings so every config value is validated and typed.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM (OpenAI) ---
    openai_api_key: str = ""
    openai_base_url: str | None = None  # allow OpenAI-compatible endpoints
    llm_model: str = "gpt-4o-mini"

    # --- Vector store (Qdrant) ---
    # Local file mode by default so it runs with zero infra.
    # Point this at http://localhost:6333 to use a running Qdrant server.
    qdrant_location: str = "./data/qdrant"
    qdrant_collection: str = "knowledge"
    embedding_model: str = "BAAI/bge-small-en-v1.5"  # local via fastembed

    # --- Agent behaviour ---
    max_tool_iterations: int = 5

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
