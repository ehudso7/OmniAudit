"""
API Middleware

Request tracking, rate limiting, authentication.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable, Optional, Dict, Any
import os
from datetime import datetime, timedelta

from ..monitoring.metrics import request_count, request_duration
from ..utils.logger import get_logger

logger = get_logger(__name__)

# JWT-related imports - handle gracefully if not installed
try:
    import jwt
    from jwt import PyJWTError
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    PyJWTError = Exception  # Fallback type


class JWTConfig:
    """JWT configuration settings."""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        try:
            self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        except ValueError:
            self.access_token_expire_minutes = 30
        self.issuer = os.getenv("JWT_ISSUER", "omniaudit")
        self.audience = os.getenv("JWT_AUDIENCE", "omniaudit-api")

    def is_configured(self) -> bool:
        """Check if JWT is properly configured."""
        return bool(self.secret_key) and JWT_AVAILABLE


jwt_config = JWTConfig()


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        Decoded token payload if valid, None otherwise
    """
    if not JWT_AVAILABLE:
        logger.warning("JWT library not available. Install with: pip install PyJWT")
        return None

    if not jwt_config.secret_key:
        logger.warning("JWT_SECRET_KEY not configured")
        return None

    try:
        payload = jwt.decode(
            token,
            jwt_config.secret_key,
            algorithms=[jwt_config.algorithm],
            issuer=jwt_config.issuer,
            audience=jwt_config.audience,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True,
                "require": ["exp", "iat", "sub"],
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"JWT decoding error: {e}")
        return None


def create_access_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT access token.

    Args:
        subject: The subject claim (usually user ID)
        additional_claims: Optional additional claims to include
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    if not JWT_AVAILABLE:
        raise RuntimeError("JWT library not available. Install with: pip install PyJWT")

    if not jwt_config.secret_key:
        raise RuntimeError("JWT_SECRET_KEY not configured")

    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=jwt_config.access_token_expire_minutes))

    to_encode = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "iss": jwt_config.issuer,
        "aud": jwt_config.audience,
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm)


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
    """JWT authentication middleware with full token validation."""

    # Paths that don't require authentication
    EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    ]

    # Paths that allow optional authentication (will proceed without token but won't set user)
    OPTIONAL_AUTH_PATHS = [
        "/api/v1/skills",
        "/api/v1/public",
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Check if authentication is optional for this path
        is_optional = any(request.url.path.startswith(path) for path in self.OPTIONAL_AUTH_PATHS)

        # In development mode only, allow requests without auth but with a dev user
        # Requires explicit opt-in via ENVIRONMENT=development
        if os.getenv("ENVIRONMENT") == "development":
            # Still try to validate token if provided
            auth_header = request.headers.get("Authorization")
            if auth_header:
                user = self._validate_token(auth_header)
                if user:
                    request.state.user = user
                else:
                    logger.warning("Invalid token in dev mode, using dev_user fallback")
                    request.state.user = {"sub": "dev_user", "role": "developer", "dev_mode": True}
            else:
                request.state.user = {"sub": "dev_user", "role": "developer", "dev_mode": True}
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            if is_optional:
                request.state.user = None
                return await call_next(request)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token
        user = self._validate_token(auth_header)
        if not user:
            if is_optional:
                request.state.user = None
                return await call_next(request)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user info to request state
        request.state.user = user

        # Log successful authentication
        logger.debug(f"Authenticated user: {user.get('sub')}")

        return await call_next(request)

    def _validate_token(self, auth_header: str) -> Optional[Dict[str, Any]]:
        """
        Validate the authorization header and extract user info.

        Args:
            auth_header: The Authorization header value

        Returns:
            User info dict if valid, None otherwise
        """
        try:
            # Parse the authorization header
            parts = auth_header.split()
            if len(parts) != 2:
                logger.warning("Invalid authorization header format")
                return None

            scheme, token = parts
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid authentication scheme: {scheme}")
                return None

            # Validate JWT token
            payload = decode_jwt_token(token)
            if not payload:
                return None

            # Extract user information from token
            user = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "permissions": payload.get("permissions", []),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
            }

            return user

        except ValueError as e:
            logger.warning(f"Token parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Authentication validation failed: {e}")
            return None


class RoleBasedAccessMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware."""

    # Define role requirements for specific paths
    ROLE_REQUIREMENTS = {
        "/api/v1/admin": ["admin"],
        "/api/v1/batch": ["admin", "operator"],
        "/api/v1/ai/enhanced": ["admin", "premium"],
    }

    async def dispatch(self, request: Request, call_next: Callable):
        # Check if the path requires specific roles
        required_roles = None
        for path_prefix, roles in self.ROLE_REQUIREMENTS.items():
            if request.url.path.startswith(path_prefix):
                required_roles = roles
                break

        if required_roles:
            user = getattr(request.state, "user", None)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication required"}
                )

            user_role = user.get("role", "user")
            if user_role not in required_roles:
                logger.warning(
                    f"Access denied for user {user.get('sub')}: "
                    f"requires {required_roles}, has {user_role}"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Insufficient permissions"}
                )

        return await call_next(request)
