from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.core.deps import require_admin
from app.schemas.auth import (
    AuditLogListResponse,
    AuditLogRead,
    AuditVerificationResponse,
)
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs_endpoint(
    event_type: Optional[str] = Query(None),
    actor_username: Optional[str] = Query(None),
    record_reference: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve paginated immutable audit log events (Administrator role required)."""
    items, total = audit_service.list_audit_logs(
        db=db,
        event_type=event_type,
        actor_username=actor_username,
        record_reference=record_reference,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[AuditLogRead.model_validate(x) for x in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/verify", response_model=AuditVerificationResponse)
def verify_audit_chain_endpoint(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Perform cryptographic verification of the SHA-256 audit log hash chain.
    Walks historical events from genesis to detect tampering, corruption, or omissions.
    Administrator role required.
    """
    result = audit_service.verify_audit_log_integrity(db)
    return AuditVerificationResponse(**result)
