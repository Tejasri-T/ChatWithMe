from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings managed via pydantic-settings."""

    # Project metadata
    PROJECT_NAME: str = "Enterprise AI Chatbot"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # LLM & Embedding Settings
    GOOGLE_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-2-preview"
    MAX_TOKENS: int = 4096

    # Persistence / Database
    DATABASE_URL: str = "sqlite:///./chatbot.db"

    # Vector Storage
    VECTOR_STORE_BACKEND: str = "faiss"  # "faiss", "qdrant", or "pgvector"
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None

    # Security & CORS
    CORS_ORIGINS: List[str] = ["*"]
    SECRET_KEY: str = "change-this-secret-key-in-production-32-chars-min"

    # Observability (Langfuse / OpenTelemetry)
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()

