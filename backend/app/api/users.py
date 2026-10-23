from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.core.deps import require_admin
from app.schemas.auth import (
    UserCreate,
    UserUpdateStatus,
    UserUpdateRole,
    UserRead,
)
from app.services import user_service
from app.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserRead])
def list_users_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve list of authorized platform accounts (Administrator role required)."""
    users, _ = user_service.list_users(db, page=page, page_size=page_size)
    return [UserRead.model_validate(u) for u in users]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user_in: UserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Provision a new role-based account (Administrator role required)."""
    try:
        user = user_service.create_user(
            db=db,
            user_in=user_in,
            actor_username=current_admin.username,
        )
        return UserRead.model_validate(user)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/{user_id}/status", response_model=UserRead)
def update_user_status_endpoint(
    user_id: int,
    status_in: UserUpdateStatus,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a platform user (Administrator role required)."""
    if current_admin.id == user_id and not status_in.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own active account.",
        )
    try:
        user = user_service.update_user_status(
            db=db,
            user_id=user_id,
            is_active=status_in.is_active,
            actor_username=current_admin.username,
        )
        return UserRead.model_validate(user)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}/role", response_model=UserRead)
def update_user_role_endpoint(
    user_id: int,
    role_in: UserUpdateRole,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Modify the platform authorization role for a user account (Administrator role required)."""
    if current_admin.id == user_id and role_in.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote their own active administrative account.",
        )
    try:
        user = user_service.update_user_role(
            db=db,
            user_id=user_id,
            new_role=role_in.role,
            actor_username=current_admin.username,
        )
        return UserRead.model_validate(user)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
