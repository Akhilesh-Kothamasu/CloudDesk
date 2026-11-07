"""Configuration settings for CloudDesk.

Provides cached application settings loaded from environment variables and
optional .env file.
"""

from functools import lru_cache
import json
import re
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _redact_url_password(url: str) -> str:
    """Mask credentials/passwords in URLs."""
    if not url:
        return url
    # Mask scheme://user:password@host
    url = re.sub(r"://([^:@/]+):([^@/]+)@", r"://\1:***@", url)
    # Mask scheme://:password@host
    url = re.sub(r"://:([^@/]+)@", r"://:***@", url)
    return url


class Settings(BaseSettings):
    """Application settings with offline-first defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General & Demo Mode
    DEMO_MODE: bool = True
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Identity & JWT
    JWT_SECRET: str = "clouddesk-insecure-demo-secret-key-change-in-production"
    SUPABASE_JWT_SECRET: str | None = None

    # Persistence & Caching
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/support.db"
    CHECKPOINT_DB_PATH: str = "./data/checkpoints.db"
    REDIS_URL: str = ""
    USE_FAKE_REDIS: bool = True

    # LLM & Models
    LLM_PROVIDER: str = "fake"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "fake"

    # Embeddings & Vector Store
    EMBEDDING_PROVIDER: str = "fake"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    VECTOR_STORE: str = "memory"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "clouddesk_knowledge"

    # Tool Execution & Policy
    APPROVAL_REQUIRED_FOR_REFUNDS: bool = True
    MAX_REFUND_WITHOUT_APPROVAL: float = 0.0
    TOOL_TIMEOUT_SECONDS: int = 30
    RATE_LIMIT_PER_MINUTE: int = 120
    SAMPLE_DATA_DIR: str = "sample_data"

    # Tracing & Observability
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "clouddesk-support"
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string, JSON string, or list."""
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    return json.loads(v_trimmed)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def effective_jwt_secret(self) -> str:
        """Return SUPABASE_JWT_SECRET if configured, otherwise JWT_SECRET."""
        if self.SUPABASE_JWT_SECRET and self.SUPABASE_JWT_SECRET.strip():
            return self.SUPABASE_JWT_SECRET
        return self.JWT_SECRET

    @property
    def is_demo(self) -> bool:
        """Whether application is running in demo mode."""
        return self.DEMO_MODE

    @property
    def is_production(self) -> bool:
        """Whether application is running in production."""
        return self.ENVIRONMENT.lower() == "production"

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Dump settings with sensitive values and URL passwords redacted."""
        data = super().model_dump(*args, **kwargs)

        sensitive_fields = {
            "JWT_SECRET",
            "SUPABASE_JWT_SECRET",
            "LLM_API_KEY",
            "QDRANT_API_KEY",
            "LANGCHAIN_API_KEY",
        }

        for field in sensitive_fields:
            if field in data and data[field]:
                data[field] = "***"

        url_fields = {
            "DATABASE_URL",
            "REDIS_URL",
            "QDRANT_URL",
        }

        for field in url_fields:
            if field in data and isinstance(data[field], str):
                data[field] = _redact_url_password(data[field])

        return data


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

