"""
API Middleware

Request tracking, rate limiting, authentication.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable
import os

from ..monitoring.metrics import request_count, request_duration
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track request metrics."""

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        response = await call_next(request)

        # Track metrics
        duration = time.time() - start_time

        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using simple in-memory counter."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limit = requests_per_minute
        self.requests = {}  # Simple in-memory storage

    async def dispatch(self, request: Request, call_next: Callable):
        # Get client identifier (IP)
        client_id = request.client.host

        # Check rate limit
        current_minute = int(time.time() / 60)
        key = f"{client_id}:{current_minute}"

        if key not in self.requests:
            self.requests[key] = 0

        self.requests[key] += 1

        # Clean old entries
        self._cleanup_old_entries(current_minute)

        if self.requests[key] > self.limit:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - self.requests[key]))

        return response

    def _cleanup_old_entries(self, current_minute: int):
        """Remove entries older than 2 minutes."""
        to_delete = []
        for key in self.requests:
            minute = int(key.split(':')[1])
            if current_minute - minute > 2:
                to_delete.append(key)

        for key in to_delete:
            del self.requests[key]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware."""

    EXCLUDED_PATHS = ["/docs", "/redoc", "/openapi.json", "/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        # For now, skip authentication in development
        if os.getenv("ENVIRONMENT") != "production":
            request.state.user = {"sub": "dev_user"}
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authorization header"}
            )

        # Validate token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")

            # TODO: Validate JWT token
            # For now, just check if token exists

            request.state.user = {"sub": "user_id"}  # Add user to request

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token"}
            )

        return await call_next(request)
