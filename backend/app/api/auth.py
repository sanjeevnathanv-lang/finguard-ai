from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.core.config import settings
from app.core.security import create_access_token
from app.core.deps import get_current_user, get_client_ip
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    PasswordChangeRequest,
    UserRead,
)
from app.services import user_service
from app.services.user_service import (
    InvalidCredentialsError,
    AccountDisabledError,
    AccountLockedError,
)
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login_endpoint(
    login_in: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials, enforce brute-force rate limits,
    and issue a signed HS256 Bearer JWT.
    """
    client_ip = get_client_ip(request)
    try:
        user = user_service.authenticate_user(
            db=db,
            identifier=login_in.username,
            plain_password=login_in.password,
            client_ip=client_ip,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except AccountDisabledError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AccountLockedError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=user.role,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.JWT_EXPIRATION_MINUTES,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve identity and permissions profile for the authenticated session."""
    return UserRead.model_validate(current_user)


@router.post("/change-password")
def change_password_endpoint(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update password for the currently authenticated account."""
    try:
        user_service.change_password(
            db=db,
            user=current_user,
            current_password=req.current_password,
            new_password=req.new_password,
        )
        return {"status": "success", "message": "Password changed successfully."}
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/logout")
def logout_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record an attributable logout event."""
    record_audit_event(
        db,
        event_type="AUTH_LOGOUT",
        actor_username=current_user.username,
        actor_role=current_user.role,
        status="SUCCESS",
        ip_address=get_client_ip(request),
    )
    return {"status": "success", "message": "Session terminated successfully."}
