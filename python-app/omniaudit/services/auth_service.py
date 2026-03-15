"""
Authentication Service

Handles user registration, login, session management, and API key auth.
Uses bcrypt for password hashing and JWT for session tokens.
"""

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import User, ApiKey
from ..utils.logger import get_logger

logger = get_logger(__name__)

# JWT secret - must be set in production
JWT_SECRET = os.getenv("JWT_SECRET", "omniaudit-dev-secret-change-in-production")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt. Production should use bcrypt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, stored_hash = password_hash.split(":", 1)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(computed.hex(), stored_hash)
    except (ValueError, AttributeError):
        return False


def _create_token(user_id: str) -> str:
    """Create a simple signed token. Production should use proper JWT."""
    import base64
    import json
    import time

    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_HOURS * 3600,
    }
    payload_bytes = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode()

    signature = hmac.new(
        JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def _decode_token(token: str) -> Optional[dict]:
    """Decode and verify a token."""
    import base64
    import json
    import time

    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None

        payload_b64, signature = parts
        expected_sig = hmac.new(
            JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


def _hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


class AuthService:
    """Authentication and user management service."""

    @staticmethod
    def register(db: Session, email: str, password: str, display_name: Optional[str] = None, role: str = "member") -> User:
        """Register a new user."""
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        user = User(
            email=email,
            password_hash=_hash_password(password),
            display_name=display_name or email.split("@")[0],
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User registered: {email}")
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> Optional[dict]:
        """Authenticate a user and return token."""
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        if not user:
            return None

        if not _verify_password(password, user.password_hash):
            return None

        user.last_login_at = datetime.utcnow()
        db.commit()

        token = _create_token(user.id)
        logger.info(f"User logged in: {email}")

        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "plan": user.plan,
            },
        }

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """Get user from a valid token."""
        payload = _decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return db.query(User).filter(User.id == user_id, User.is_active == True).first()

    @staticmethod
    def get_user_from_api_key(db: Session, key: str) -> Optional[User]:
        """Get user from an API key."""
        key_hash = _hash_api_key(key)
        api_key = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash, ApiKey.is_active == True
        ).first()

        if not api_key:
            return None

        api_key.last_used_at = datetime.utcnow()
        db.commit()

        return db.query(User).filter(User.id == api_key.user_id, User.is_active == True).first()

    @staticmethod
    def create_api_key(db: Session, user_id: str, name: str = "default") -> dict:
        """Create a new API key for a user."""
        raw_key = f"oa_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:7]

        api_key = ApiKey(
            user_id=user_id,
            key_hash=_hash_api_key(raw_key),
            name=name,
            prefix=prefix,
        )
        db.add(api_key)
        db.commit()

        return {
            "key": raw_key,  # Only shown once
            "id": api_key.id,
            "prefix": prefix,
            "name": name,
        }

    @staticmethod
    def ensure_default_admin(db: Session):
        """Create a default admin user if no users exist."""
        if db.query(User).count() > 0:
            return None

        admin_email = os.getenv("OMNIAUDIT_ADMIN_EMAIL", "admin@omniaudit.local")
        admin_password = os.getenv("OMNIAUDIT_ADMIN_PASSWORD", "changeme123!")

        try:
            user = AuthService.register(
                db, admin_email, admin_password,
                display_name="Admin", role="admin"
            )
            logger.info(f"Default admin created: {admin_email}")
            return user
        except ValueError:
            return None
