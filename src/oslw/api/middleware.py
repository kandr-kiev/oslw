"""Rate limiting middleware for OSLW API.

Provides sliding window rate limiting using in-memory store.
Configurable per-endpoint via decorator or middleware.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from oslw.config.logging import get_logger

logger = get_logger("oslw.api.middleware")


@dataclass
class RateLimitConfig:
    """Rate limit configuration.

    Attributes:
        max_requests: Maximum requests allowed in the window
        window_seconds: Time window in seconds
        key_func: Function to extract client identifier from request
    """
    max_requests: int = 60
    window_seconds: int = 60
    key_func: Callable[[Request], str] = None


class RateLimiter:
    """In-memory sliding window rate limiter.

    Usage:
        limiter = RateLimiter(max_requests=100, window_seconds=60)

        # As middleware:
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            return await limiter.middleware(request, call_next)

        # Or as decorator:
        @limiter.limit(max_requests=10, window_seconds=30)
        async def heavy_endpoint():
            ...
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        key_func: Callable[[Request], str] = None,
    ):
        self.default_config = RateLimitConfig(
            max_requests=max_requests,
            window_seconds=window_seconds,
            key_func=key_func,
        )
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str, window: int) -> None:
        """Remove expired entries for a key."""
        cutoff = time.time() - window
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]

    def check(self, request: Request, config: RateLimitConfig = None) -> dict:
        """Check if request is within rate limit.

        Returns:
            Dict with 'allowed' (bool) and 'limits' (dict)
        """
        config = config or self.default_config

        # Default key function: use client IP
        key_func = config.key_func or (lambda r: r.client.host if r.client else "unknown")
        key = key_func(request)
        self._cleanup(key, config.window_seconds)

        current_count = len(self._requests[key])
        allowed = current_count < config.max_requests

        if allowed:
            self._requests[key].append(time.time())

        return {
            "allowed": allowed,
            "limits": {
                "max_requests": config.max_requests,
                "window_seconds": config.window_seconds,
                "remaining": max(0, config.max_requests - current_count - (1 if allowed else 0)),
                "reset": int(time.time()) + config.window_seconds,
            },
        }

    async def middleware(self, request: Request, call_next) -> Response:
        """FastAPI middleware for rate limiting."""
        result = self.check(request)

        if not result["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limits": result["limits"],
                },
                headers={
                    "X-RateLimit-Limit": str(result["limits"]["max_requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result["limits"]["reset"]),
                    "Retry-After": str(result["limits"]["reset"] - int(time.time())),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(result["limits"]["max_requests"])
        response.headers["X-RateLimit-Remaining"] = str(result["limits"]["remaining"])
        response.headers["X-RateLimit-Reset"] = str(result["limits"]["reset"])

        return response

    def limit(self, max_requests: int = None, window_seconds: int = None):
        """Decorator for endpoint-level rate limiting."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request from kwargs or args
                request = kwargs.get("request")
                if request is None:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break

                if request is None:
                    # No request found, skip rate limiting
                    return await func(*args, **kwargs)

                config = RateLimitConfig(
                    max_requests=max_requests or self.default_config.max_requests,
                    window_seconds=window_seconds or self.default_config.window_seconds,
                )
                result = self.check(request, config)

                if not result["allowed"]:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded", "limits": result["limits"]},
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Default rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


def get_rate_limiter() -> RateLimiter:
    """Get the default rate limiter instance."""
    return rate_limiter
