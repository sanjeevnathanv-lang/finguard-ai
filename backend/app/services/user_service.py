import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import User
from app.core.security import hash_password, verify_password, login_rate_limiter, VALID_ROLES
from app.schemas.auth import UserCreate
from app.services.audit_service import record_audit_event

logger = logging.getLogger("finguard.users")


class AuthenticationError(Exception):
    pass


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, message: str = "Invalid username or password."):
        super().__init__(message)


class AccountDisabledError(AuthenticationError):
    def __init__(self, message: str = "Account is disabled. Contact your system administrator."):
        super().__init__(message)


class AccountLockedError(AuthenticationError):
    def __init__(self, remaining_seconds: int):
        self.remaining_seconds = remaining_seconds
        minutes = max(1, remaining_seconds // 60)
        super().__init__(
            f"Too many failed login attempts. Account temporarily locked for {minutes} minute(s)."
        )


class UserAlreadyExistsError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"A user with this {field} ('{value}') already exists.")


class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found.")


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieve user by database primary key."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username_or_email(db: Session, identifier: str) -> Optional[User]:
    """Lookup user by case-insensitive username or email."""
    norm = identifier.strip().lower()
    return db.query(User).filter(
        or_(User.username == norm, User.email == norm)
    ).first()


def authenticate_user(
    db: Session,
    identifier: str,
    plain_password: str,
    client_ip: Optional[str] = None,
) -> User:
    """
    Authenticate user credentials with rate-limiting, timing-safe bcrypt checks,
    account status validation, and attributable security audit logging.
    """
    rate_key = f"{client_ip or 'unknown'}:{identifier.strip().lower()}"

    # 1. Rate-limit check
    is_locked, remaining = login_rate_limiter.is_locked(rate_key)
    if is_locked:
        record_audit_event(
            db,
            event_type="AUTH_LOGIN_RATE_LIMITED",
            actor_username=identifier.strip().lower(),
            status="FAILURE",
            ip_address=client_ip,
            metadata={"remaining_lock_seconds": remaining},
        )
        raise AccountLockedError(remaining)

    # 2. User lookup
    user = get_user_by_username_or_email(db, identifier)
    if not user:
        login_rate_limiter.record_failure(rate_key)
        record_audit_event(
            db,
            event_type="AUTH_LOGIN_FAILED",
            actor_username=identifier.strip().lower(),
            status="FAILURE",
            ip_address=client_ip,
            metadata={"reason": "User not found"},
        )
        raise InvalidCredentialsError()

    # 3. Account enabled check
    if not user.is_active:
        record_audit_event(
            db,
            event_type="AUTH_LOGIN_DISABLED_REJECTED",
            actor_username=user.username,
            actor_role=user.role,
            status="FAILURE",
            ip_address=client_ip,
            metadata={"reason": "Account inactive"},
        )
        raise AccountDisabledError()

    # 4. Password verification
    if not verify_password(plain_password, user.password_hash):
        is_locked_now, lock_secs = login_rate_limiter.record_failure(rate_key)
        user.failed_login_attempts += 1
        db.commit()

        record_audit_event(
            db,
            event_type="AUTH_LOGIN_FAILED",
            actor_username=user.username,
            actor_role=user.role,
            status="FAILURE",
            ip_address=client_ip,
            metadata={
                "failed_attempts": user.failed_login_attempts,
                "is_locked_now": is_locked_now,
            },
        )
        if is_locked_now:
            raise AccountLockedError(lock_secs)
        raise InvalidCredentialsError()

    # 5. Success
    login_rate_limiter.record_success(rate_key)
    now = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    user.last_login_at = now
    db.commit()

    record_audit_event(
        db,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_username=user.username,
        actor_role=user.role,
        status="SUCCESS",
        ip_address=client_ip,
    )
    return user


def create_user(
    db: Session,
    user_in: UserCreate,
    actor_username: str = "SYSTEM",
) -> User:
    """Create a new user with bcrypt password hashing and uniqueness validation."""
    norm_username = user_in.username.strip().lower()
    norm_email = user_in.email.strip().lower()

    if db.query(User.id).filter(User.username == norm_username).first():
        raise UserAlreadyExistsError("username", norm_username)
    if db.query(User.id).filter(User.email == norm_email).first():
        raise UserAlreadyExistsError("email", norm_email)

    now = datetime.now(timezone.utc)
    user = User(
        username=norm_username,
        email=norm_email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role.upper(),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db,
        event_type="USER_CREATED",
        actor_username=actor_username,
        record_reference=user.username,
        status="SUCCESS",
        metadata={"user_id": user.id, "role": user.role, "email": user.email},
    )
    return user


def update_user_status(
    db: Session,
    user_id: int,
    is_active: bool,
    actor_username: str = "SYSTEM",
) -> User:
    """Enable or deactivate a user account."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(user_id)

    old_status = user.is_active
    user.is_active = is_active
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db,
        event_type="USER_STATUS_UPDATED",
        actor_username=actor_username,
        record_reference=user.username,
        status="SUCCESS",
        metadata={"user_id": user.id, "old_active": old_status, "new_active": is_active},
    )
    return user


def update_user_role(
    db: Session,
    user_id: int,
    new_role: str,
    actor_username: str = "SYSTEM",
) -> User:
    """Modify the platform authorization role for a user account."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(user_id)

    role_upper = new_role.strip().upper()
    if role_upper not in VALID_ROLES:
        raise ValueError(f"Invalid role '{new_role}'. Must be one of {sorted(VALID_ROLES)}")

    old_role = user.role
    user.role = role_upper
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db,
        event_type="USER_ROLE_UPDATED",
        actor_username=actor_username,
        record_reference=user.username,
        status="SUCCESS",
        metadata={
            "user_id": user.id,
            "old_role": old_role,
            "new_role": role_upper,
        },
    )
    return user


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> bool:
    """Verify current password and safely update to a new bcrypt hash."""
    if not verify_password(current_password, user.password_hash):
        record_audit_event(
            db,
            event_type="PASSWORD_CHANGE_FAILED",
            actor_username=user.username,
            status="FAILURE",
            metadata={"reason": "Incorrect current password"},
        )
        raise InvalidCredentialsError("Current password verification failed.")

    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    record_audit_event(
        db,
        event_type="PASSWORD_CHANGED",
        actor_username=user.username,
        actor_role=user.role,
        status="SUCCESS",
    )
    return True


def list_users(db: Session, page: int = 1, page_size: int = 50) -> Tuple[List[User], int]:
    """List registered users ordered by creation date."""
    query = db.query(User)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(User.id.asc()).offset(offset).limit(page_size).all()
    return items, total


def seed_default_users_if_empty(db: Session) -> None:
    """
    Idempotent initial user provisioning for local academic prototype.
    If the users table has zero records, creates initial Administrator, Analyst,
    and Viewer accounts using passwords defined via environment variables or safe defaults.
    """
    count = db.query(User.id).count()
    if count > 0:
        return

    logger.info("Initializing baseline role-based accounts (Admin, Analyst, Viewer)...")
    admin_pwd = os.getenv("INITIAL_ADMIN_PASSWORD", "FinGuard@Admin2026!")
    analyst_pwd = os.getenv("INITIAL_ANALYST_PASSWORD", "FinGuard@Analyst2026!")
    viewer_pwd = os.getenv("INITIAL_VIEWER_PASSWORD", "FinGuard@Viewer2026!")

    initial_users = [
        UserCreate(
            username="admin",
            email="admin@finguard.ai",
            password=admin_pwd,
            full_name="System Administrator",
            role="ADMIN",
        ),
        UserCreate(
            username="analyst",
            email="analyst@finguard.ai",
            password=analyst_pwd,
            full_name="Risk Investigator",
            role="ANALYST",
        ),
        UserCreate(
            username="viewer",
            email="viewer@finguard.ai",
            password=viewer_pwd,
            full_name="Audit Viewer",
            role="VIEWER",
        ),
    ]

    for u_in in initial_users:
        create_user(db, u_in, actor_username="SYSTEM_BOOTSTRAP")

    logger.info("Default role-based accounts provisioned successfully.")
