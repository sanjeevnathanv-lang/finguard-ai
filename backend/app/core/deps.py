from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.core.security import decode_access_token
from app.services.user_service import get_user_by_id

security_bearer = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """Extract client IP safely from request or proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate incoming Bearer JWT and return the authenticated User model.
    Raises 401 Unauthorized if missing, expired, or invalid.
    """
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth_header.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Access denied.",
        )

    return user


def require_role(allowed_roles: List[str]):
    """Role-based access control dependency factory."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions. Required role: one of {sorted(allowed_roles)}. "
                    f"Current account role: {current_user.role}."
                ),
            )
        return current_user

    return role_checker


# Convenient role dependency shortcuts
require_admin = require_role(["ADMIN"])
require_analyst = require_role(["ADMIN", "ANALYST"])
require_viewer = require_role(["ADMIN", "ANALYST", "VIEWER"])
