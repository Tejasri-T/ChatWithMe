from functools import lru_cache

from pydantic import model_validator
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
    # Accepts either GOOGLE_API_KEY or GEMINI_API_KEY from the environment
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""          # alias used in .env
    LLM_MODEL: str = "gemini-3.8-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-2-preview"
    MAX_TOKENS: int = 4096

    @model_validator(mode="after")
    def _resolve_api_key(self) -> "Settings":
        """Promote GEMINI_API_KEY → GOOGLE_API_KEY when needed."""
        if not self.GOOGLE_API_KEY and self.GEMINI_API_KEY:
            self.GOOGLE_API_KEY = self.GEMINI_API_KEY
        return self

    # Persistence / Database
    # Use postgresql+psycopg:// for SQLAlchemy-style drivers; DATABASE_URL_RAW is
    # the plain postgresql:// URL consumed by psycopg / LangGraph directly.
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/chatWithMe"
    DATABASE_URL_RAW: str = "postgresql://postgres:password@localhost:5432/chatWithMe"

    # Vector Storage
    VECTOR_STORE_BACKEND: str = "faiss"  # "faiss", "qdrant", or "pgvector"
    QDRANT_URL: str | None = None
    QDRANT_API_KEY: str | None = None

    # Security, Auth & Guardrails
    CORS_ORIGINS: list[str] = ["*"]
    SECRET_KEY: str = "change-this-secret-key-in-production-32-chars-min"
    API_KEY_AUTH_ENABLED: bool = False
    API_AUTH_KEY: str | None = None
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_PROMPT_LENGTH: int = 8000
    RATE_LIMIT_PER_MINUTE: int = 60

    # Observability (Langfuse / OpenTelemetry)
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()

