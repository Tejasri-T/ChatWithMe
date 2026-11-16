"""Security, authentication, and request guardrails."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str | None:
    """Validate incoming API key when authentication is enabled in settings."""
    settings = get_settings()
    if not settings.API_KEY_AUTH_ENABLED:
        return None

    if not api_key or api_key != settings.API_AUTH_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
        )
    return api_key


def validate_pdf_content(content: bytes) -> bool:
    """
    Verify that uploaded bytes contain a valid PDF magic header.
    Valid PDFs begin with %PDF- within the first 1024 bytes.
    """
    if not content or len(content) < 5:
        return False
    header_sample = content[:1024]
    return b"%PDF-" in header_sample


class RateLimiter:
    """Thread-safe sliding-window in-memory rate limiter per client IP."""

    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, client_ip: str) -> None:
        """Record a request and raise HTTP 429 if client exceeds limits."""
        now = time.time()
        window_start = now - 60.0

        with self._lock:
            # Purge timestamps older than 60 seconds
            self._requests[client_ip] = [
                ts for ts in self._requests[client_ip] if ts > window_start
            ]

            if len(self._requests[client_ip]) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: maximum {self.limit} requests per minute.",
                    headers={"Retry-After": "60"},
                )

            self._requests[client_ip].append(now)


_rate_limiter = RateLimiter(requests_per_minute=get_settings().RATE_LIMIT_PER_MINUTE)


def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency enforcing per-client rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    _rate_limiter.check(client_ip)
