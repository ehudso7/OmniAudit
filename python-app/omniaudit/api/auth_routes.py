"""
Authentication API Routes

Endpoints for user registration, login, and account management.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import User
from ..services.auth_service import AuthService
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateApiKeyRequest(BaseModel):
    name: str = "default"


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Extract current user from Authorization header or X-API-Key.
    Returns None if no auth provided (for optional auth endpoints).
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user = AuthService.get_user_from_token(db, token)
        if user:
            return user

    if x_api_key:
        user = AuthService.get_user_from_api_key(db, x_api_key)
        if user:
            return user

    return None


def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Dependency that requires authentication."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_admin(
    user: User = Depends(require_user),
) -> User:
    """Dependency that requires admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Register a new user account."""
    try:
        user = AuthService.register(db, request.email, request.password, request.display_name)
        login_result = AuthService.login(db, request.email, request.password)
        return {
            "user": login_result["user"],
            "token": login_result["token"],
            "message": "Account created successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Login with email and password."""
    result = AuthService.login(db, request.email, request.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return result


@router.get("/me")
async def get_me(user: User = Depends(require_user)) -> Dict[str, Any]:
    """Get current user profile."""
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "plan": user.plan,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() + "Z" if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() + "Z" if user.last_login_at else None,
            "notify_run_complete": user.notify_run_complete,
            "notify_release_blocked": user.notify_release_blocked,
            "notify_critical_issues": user.notify_critical_issues,
        }
    }


@router.put("/me")
async def update_me(
    updates: Dict[str, Any],
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Update current user profile."""
    allowed = {"display_name", "notify_run_complete", "notify_release_blocked", "notify_critical_issues"}
    for key, value in updates.items():
        if key in allowed:
            setattr(user, key, value)
    db.commit()
    return {"message": "Profile updated"}


@router.post("/api-keys")
async def create_api_key(
    request: CreateApiKeyRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create a new API key."""
    result = AuthService.create_api_key(db, user.id, request.name)
    return {
        "api_key": result,
        "message": "API key created. Save the key - it will not be shown again.",
    }


@router.get("/api-keys")
async def list_api_keys(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """List user's API keys (without the actual key values)."""
    from ..db.models import ApiKey
    keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).all()
    return {
        "api_keys": [
            {
                "id": k.id,
                "prefix": k.prefix,
                "name": k.name,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at.isoformat() + "Z" if k.last_used_at else None,
                "created_at": k.created_at.isoformat() + "Z" if k.created_at else None,
            }
            for k in keys
        ]
    }
