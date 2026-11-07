"""Unit tests for backend.app.core.config."""

import os
import unittest

from backend.app.core.config import Settings, get_settings


class TestConfig(unittest.TestCase):
    """Test suite for application settings."""

    def test_default_offline_settings(self):
        """Verify default settings support offline-first execution."""
        settings = Settings()

        self.assertTrue(settings.DEMO_MODE)
        self.assertTrue(settings.is_demo)
        self.assertFalse(settings.is_production)
        self.assertEqual(settings.ENVIRONMENT, "development")

        # Offline provider defaults
        self.assertEqual(settings.LLM_PROVIDER, "fake")
        self.assertEqual(settings.VECTOR_STORE, "memory")
        self.assertTrue(settings.USE_FAKE_REDIS)
        self.assertEqual(settings.EMBEDDING_PROVIDER, "fake")

        # Persistence & Policy defaults
        self.assertEqual(settings.DATABASE_URL, "sqlite+aiosqlite:///./data/support.db")
        self.assertEqual(settings.CHECKPOINT_DB_PATH, "./data/checkpoints.db")
        self.assertTrue(settings.APPROVAL_REQUIRED_FOR_REFUNDS)
        self.assertEqual(settings.MAX_REFUND_WITHOUT_APPROVAL, 0.0)
        self.assertEqual(settings.RATE_LIMIT_PER_MINUTE, 120)

    def test_effective_jwt_secret_precedence(self):
        """Supabase JWT secret takes precedence over default JWT_SECRET when set."""
        settings_default = Settings(JWT_SECRET="local-secret", SUPABASE_JWT_SECRET=None)
        self.assertEqual(settings_default.effective_jwt_secret, "local-secret")

        settings_supabase = Settings(
            JWT_SECRET="local-secret",
            SUPABASE_JWT_SECRET="supabase-shared-secret",
        )
        self.assertEqual(settings_supabase.effective_jwt_secret, "supabase-shared-secret")

    def test_cors_origins_parsing(self):
        """Verify CORS_ORIGINS parses list, comma-separated string, or JSON array."""
        settings_str = Settings(CORS_ORIGINS="http://localhost:3000,http://example.com")
        self.assertEqual(settings_str.CORS_ORIGINS, ["http://localhost:3000", "http://example.com"])

        settings_json = Settings(CORS_ORIGINS='["http://localhost:8000"]')
        self.assertEqual(settings_json.CORS_ORIGINS, ["http://localhost:8000"])

        settings_list = Settings(CORS_ORIGINS=["http://localhost:3000"])
        self.assertEqual(settings_list.CORS_ORIGINS, ["http://localhost:3000"])

    def test_model_dump_redacts_secrets_and_passwords(self):
        """model_dump() must redact secrets and URL passwords while attributes retain raw values."""
        raw_db_url = "postgresql+asyncpg://admin:super_secret_pw@db.internal:5432/clouddesk"
        raw_redis_url = "redis://:redis_secret_pw@cache.internal:6379/0"
        raw_jwt = "my-secret-jwt-key"
        raw_llm_key = "sk-llm-api-key"

        settings = Settings(
            DATABASE_URL=raw_db_url,
            REDIS_URL=raw_redis_url,
            JWT_SECRET=raw_jwt,
            SUPABASE_JWT_SECRET="supa-secret",
            LLM_API_KEY=raw_llm_key,
            QDRANT_API_KEY="qdrant-secret",
            LANGCHAIN_API_KEY="langchain-secret",
        )

        # Connection code accessing attributes directly gets unredacted values
        self.assertEqual(settings.DATABASE_URL, raw_db_url)
        self.assertEqual(settings.REDIS_URL, raw_redis_url)
        self.assertEqual(settings.JWT_SECRET, raw_jwt)
        self.assertEqual(settings.LLM_API_KEY, raw_llm_key)

        # model_dump() returns redacted dictionary
        dumped = settings.model_dump()

        self.assertEqual(dumped["JWT_SECRET"], "***")
        self.assertEqual(dumped["SUPABASE_JWT_SECRET"], "***")
        self.assertEqual(dumped["LLM_API_KEY"], "***")
        self.assertEqual(dumped["QDRANT_API_KEY"], "***")
        self.assertEqual(dumped["LANGCHAIN_API_KEY"], "***")

        self.assertEqual(
            dumped["DATABASE_URL"],
            "postgresql+asyncpg://admin:***@db.internal:5432/clouddesk",
        )
        self.assertEqual(
            dumped["REDIS_URL"],
            "redis://:***@cache.internal:6379/0",
        )

    def test_get_settings_cached(self):
        """get_settings() returns a cached singleton instance."""
        s1 = get_settings()
        s2 = get_settings()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()

