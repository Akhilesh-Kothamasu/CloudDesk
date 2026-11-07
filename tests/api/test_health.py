"""Tests for health routes and RequestIdMiddleware."""

import json
from typing import Any, Coroutine
import unittest
import uuid

from fastapi import status
from starlette.requests import Request
from starlette.responses import Response

from backend.app.api.health import health, health_live, health_ready
from backend.app.core.config import Settings
from backend.app.core.logging import get_request_id
from backend.app.main import app, create_app
from backend.app.middleware.request_id import RequestIdMiddleware, is_safe_request_id


def run_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run an async coroutine synchronously without socket loop overhead."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    raise RuntimeError("Coroutine did not complete synchronously")


class TestHealthRoutes(unittest.TestCase):
    """Test suite for /health, /health/live, /health/ready endpoints."""

    def test_health_endpoint(self):
        """GET /health returns 200 with service metadata."""
        settings = Settings()
        data = run_sync(health(settings))

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "clouddesk")
        self.assertEqual(data["version"], "0.1.0")
        self.assertEqual(data["environment"], "development")

    def test_health_live_endpoint(self):
        """GET /health/live returns 200 alive without dependency I/O."""
        data = run_sync(health_live())
        self.assertEqual(data, {"status": "alive"})

    def test_health_ready_default_offline_ok(self):
        """GET /health/ready returns 200 ready under default offline configuration."""
        settings = Settings()
        response: Response = run_sync(health_ready(settings))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["status"], "ready")

        checks = data["checks"]
        self.assertEqual(checks["database"]["status"], "ok")
        self.assertEqual(checks["redis"]["status"], "ok")
        self.assertEqual(checks["vector_store"]["status"], "ok")
        self.assertEqual(checks["llm"]["status"], "ok")

    def test_health_ready_degraded_when_database_unconfigured(self):
        """GET /health/ready returns 503 degraded when database URL is empty."""
        settings = Settings(DATABASE_URL="")
        response: Response = run_sync(health_ready(settings))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["checks"]["database"]["status"], "error")
        self.assertIn("detail", data["checks"]["database"])

    def test_health_ready_degraded_when_redis_unconfigured(self):
        """GET /health/ready returns 503 degraded when redis URL is empty and fake redis is off."""
        settings = Settings(USE_FAKE_REDIS=False, REDIS_URL="")
        response: Response = run_sync(health_ready(settings))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["checks"]["redis"]["status"], "error")

    def test_health_ready_degraded_when_qdrant_unconfigured(self):
        """GET /health/ready returns 503 degraded when vector store is qdrant but URL is empty."""
        settings = Settings(VECTOR_STORE="qdrant", QDRANT_URL="")
        response: Response = run_sync(health_ready(settings))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["checks"]["vector_store"]["status"], "error")

    def test_health_ready_degraded_when_llm_key_missing(self):
        """GET /health/ready returns 503 degraded when provider requires API key but none provided."""
        settings = Settings(LLM_PROVIDER="openai", LLM_API_KEY="")
        response: Response = run_sync(health_ready(settings))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["checks"]["llm"]["status"], "error")

    def test_health_ready_details_never_leak_sensitive_data(self):
        """Check details never contain credentials, passwords, or full secret URLs."""
        settings = Settings(
            DATABASE_URL="",
            USE_FAKE_REDIS=False,
            REDIS_URL="",
            VECTOR_STORE="qdrant",
            QDRANT_URL="",
            LLM_PROVIDER="openai",
            LLM_API_KEY="",
        )
        response: Response = run_sync(health_ready(settings))
        body_text = response.body.decode("utf-8")

        for forbidden in ["password", "secret", "Bearer", "sk-", "key="]:
            self.assertNotIn(forbidden, body_text.lower())


class TestRequestIdMiddleware(unittest.TestCase):
    """Test suite for RequestIdMiddleware and validation helpers."""

    def setUp(self):
        self.middleware = RequestIdMiddleware(app=None)

    def test_is_safe_request_id(self):
        """Verify is_safe_request_id strictly enforces 1-128 safe characters."""
        self.assertTrue(is_safe_request_id("valid-id_123.456:ok"))
        self.assertTrue(is_safe_request_id("a" * 128))

        self.assertFalse(is_safe_request_id(""))
        self.assertFalse(is_safe_request_id("a" * 129))
        self.assertFalse(is_safe_request_id("<script>"))
        self.assertFalse(is_safe_request_id("has space"))
        self.assertFalse(is_safe_request_id("has\newline"))
        self.assertFalse(is_safe_request_id(None))

    def test_middleware_echoes_safe_caller_header(self):
        """Middleware echoes safe client-supplied X-Request-ID header."""
        custom_id = "trace-req_123.456"

        async def fake_endpoint(req: Request) -> Response:
            return Response(content="ok", status_code=200)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", custom_id.encode("utf-8"))],
        }
        request = Request(scope=scope)
        response = run_sync(self.middleware.dispatch(request, fake_endpoint))

        self.assertEqual(response.headers.get("X-Request-ID"), custom_id)

    def test_middleware_generates_uuid_when_omitted(self):
        """Middleware assigns a valid UUID4 when X-Request-ID header is omitted."""

        async def fake_endpoint(req: Request) -> Response:
            return Response(content="ok", status_code=200)

        scope = {"type": "http", "headers": []}
        request = Request(scope=scope)
        response = run_sync(self.middleware.dispatch(request, fake_endpoint))

        generated_id = response.headers.get("X-Request-ID")
        self.assertIsNotNone(generated_id)
        parsed = uuid.UUID(generated_id, version=4)
        self.assertEqual(str(parsed), generated_id)

    def test_middleware_replaces_unsafe_header(self):
        """Middleware replaces unsafe caller header with a new UUID4."""
        unsafe_id = "<script>alert('xss')</script>"

        async def fake_endpoint(req: Request) -> Response:
            return Response(content="ok", status_code=200)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", unsafe_id.encode("utf-8"))],
        }
        request = Request(scope=scope)
        response = run_sync(self.middleware.dispatch(request, fake_endpoint))

        header_val = response.headers.get("X-Request-ID")
        self.assertNotEqual(header_val, unsafe_id)
        parsed = uuid.UUID(header_val, version=4)
        self.assertEqual(str(parsed), header_val)

    def test_middleware_binds_log_context_and_request_state(self):
        """Middleware binds request_id to log_context and request.state during execution."""
        captured_log_req_id = None
        captured_state_req_id = None

        async def fake_endpoint(req: Request) -> Response:
            nonlocal captured_log_req_id, captured_state_req_id
            captured_log_req_id = get_request_id()
            captured_state_req_id = req.state.request_id
            return Response(content="ok", status_code=200)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", b"trace-context-test")],
        }
        request = Request(scope=scope)
        run_sync(self.middleware.dispatch(request, fake_endpoint))

        self.assertEqual(captured_log_req_id, "trace-context-test")
        self.assertEqual(captured_state_req_id, "trace-context-test")


class TestApplicationWiring(unittest.TestCase):
    """Test suite for FastAPI application assembly, routes, and middleware registration."""

    def test_app_routes_registered(self):
        """Verify health routes are registered unprefixed on app."""
        route_paths = [getattr(route, "path", None) for route in app.routes]

        self.assertIn("/health", route_paths)
        self.assertIn("/health/live", route_paths)
        self.assertIn("/health/ready", route_paths)

    def test_middlewares_registered(self):
        """Verify RequestIdMiddleware and CORSMiddleware are registered in app."""
        test_app = create_app()
        middleware_classes = [m.cls for m in test_app.user_middleware]

        self.assertIn(RequestIdMiddleware, middleware_classes)
        from fastapi.middleware.cors import CORSMiddleware

        self.assertIn(CORSMiddleware, middleware_classes)


if __name__ == "__main__":
    unittest.main()
