"""Tests for rate limiting middleware."""

import time
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from oslw.api.middleware import RateLimiter, rate_limiter


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_default_limit(self):
        """Default: 60 requests per 60 seconds."""
        limiter = RateLimiter()
        assert limiter.default_config.max_requests == 60
        assert limiter.default_config.window_seconds == 60

    def test_custom_limit(self):
        """Custom config: 10 requests per 30 seconds."""
        limiter = RateLimiter(max_requests=10, window_seconds=30)
        assert limiter.default_config.max_requests == 10
        assert limiter.default_config.window_seconds == 30

    def test_check_allowed(self):
        """First request should be allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"

        result = limiter.check(mock_request)
        assert result["allowed"] is True
        assert result["limits"]["remaining"] == 4

    def test_check_blocked(self):
        """Should block after max_requests exceeded."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"

        for _ in range(3):
            limiter.check(mock_request)

        result = limiter.check(mock_request)
        assert result["allowed"] is False
        assert result["limits"]["remaining"] == 0

    def test_cleanup_expired(self):
        """Expired entries should be cleaned up."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"

        # Fill up
        limiter.check(mock_request)
        limiter.check(mock_request)

        # Should be blocked
        result = limiter.check(mock_request)
        assert result["allowed"] is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        result = limiter.check(mock_request)
        assert result["allowed"] is True

    def test_different_clients(self):
        """Different client IPs should have separate limits."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        client_a = MagicMock(spec=Request)
        client_a.client.host = "10.0.0.1"
        client_b = MagicMock(spec=Request)
        client_b.client.host = "10.0.0.2"

        # Client A uses its limit
        limiter.check(client_a)
        assert limiter.check(client_a)["allowed"] is False

        # Client B should still be allowed
        assert limiter.check(client_b)["allowed"] is True


class TestRateLimiterMiddleware:
    """Tests for middleware integration."""

    def test_middleware_allowed(self):
        """Middleware should allow requests within limit."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app.middleware("http")(rate_limiter.middleware)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_middleware_blocked(self):
        """Middleware should return 429 when limit exceeded."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        app = FastAPI()
        app.middleware("http")(limiter.middleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        # Use up the limit
        client.get("/test")
        client.get("/test")

        # Third should be blocked
        response = client.get("/test")
        assert response.status_code == 429
        data = response.json()
        assert "Rate limit exceeded" in data["detail"]
        assert "Retry-After" in response.headers

    def test_middleware_headers(self):
        """Middleware should add rate limit headers."""
        app = FastAPI()
        app.middleware("http")(rate_limiter.middleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
