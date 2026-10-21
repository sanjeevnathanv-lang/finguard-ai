from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.security import VALID_ROLES


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, description="Username or email address")
    password: str = Field(..., min_length=1, max_length=128, description="Plaintext password for verification")


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (minimum 8 characters)")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=128)
    role: str = Field(default="ANALYST")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean.isalnum() and "_" not in clean and "-" not in clean and "." not in clean:
            raise ValueError("Username may only contain letters, numbers, underscores, dots, or dashes.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean:
            raise ValueError("Invalid email format.")
        return clean

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in VALID_ROLES:
            raise ValueError(f"Role must be one of {sorted(VALID_ROLES)}")
        return upper


class UserUpdateStatus(BaseModel):
    is_active: bool


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserRead


class AuditLogRead(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    actor_username: str
    actor_role: Optional[str] = None
    record_reference: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    metadata_json: Optional[str] = None
    previous_hash: Optional[str] = None
    event_hash: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogRead]
    total: int
    page: int
    page_size: int


class AuditVerificationResponse(BaseModel):
    is_valid: bool
    total_records_checked: int
    status: str
    message: str
    tampered_record_id: Optional[int] = None
    latest_hash: Optional[str] = None
