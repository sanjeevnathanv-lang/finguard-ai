import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionPaginatedResponse,
    CSVUploadResponse,
)
from app.services import transaction_service
from app.services.transaction_service import (
    DuplicateReferenceError,
    CSVValidationError,
)
from app.core.deps import require_analyst, require_viewer
from app.db.models import User
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("", response_model=TransactionPaginatedResponse)
def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search term for reference / sender / receiver"),
    status: Optional[str] = Query(default=None, description="Filter by status (COMPLETED, PENDING, FLAGGED, etc.)"),
    currency: Optional[str] = Query(default=None, description="Filter by currency (INR, USD, etc.)"),
    transaction_type: Optional[str] = Query(default=None, description="Filter by type (PAYMENT, TRANSFER, etc.)"),
    channel: Optional[str] = Query(default=None, description="Filter by channel (ONLINE, MOBILE_APP, ATM, etc.)"),
    start_date: Optional[datetime] = Query(default=None, description="Filter from timestamp"),
    end_date: Optional[datetime] = Query(default=None, description="Filter until timestamp"),
    sort_by: str = Query(default="timestamp", description="Sort column (timestamp, amount, reference, status)"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve paginated transactions with flexible filtering and stable ordering."""
    items, total = transaction_service.get_transactions_paginated(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        currency=currency,
        transaction_type=transaction_type,
        channel=channel,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return TransactionPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve transaction details by primary key."""
    txn = transaction_service.get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found."
        )
    return txn


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Create a new transaction record."""
    try:
        txn = transaction_service.create_transaction(db, payload)
        record_audit_event(
            db,
            event_type="TRANSACTION_CREATED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=txn.reference,
            status="SUCCESS",
            metadata={"amount": float(txn.amount), "currency": txn.currency},
        )
        return txn
    except DuplicateReferenceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/upload", response_model=CSVUploadResponse)
async def upload_transactions_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Securely upload and ingest transactions from a CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are accepted."
        )

    try:
        content_bytes = await file.read()
        res = transaction_service.import_transactions_from_csv(
            db=db,
            content_bytes=content_bytes,
            filename=file.filename,
        )
        record_audit_event(
            db,
            event_type="TRANSACTION_CSV_UPLOADED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=res.import_reference,
            status="SUCCESS",
            metadata={
                "filename": file.filename,
                "imported_rows": res.imported_rows,
                "rejected_rows": res.rejected_rows,
            },
        )
        return res
    except CSVValidationError as e:
        record_audit_event(
            db,
            event_type="TRANSACTION_CSV_REJECTED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            status="FAILURE",
            metadata={"filename": file.filename, "error": e.message},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV file: {str(e)}",
        )


@router.post("/reset")
def reset_all_transactions(
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Purge all transaction records and operational history."""
    try:
        return transaction_service.reset_transactions_and_data(
            db=db,
            actor_username=current_user.username,
            actor_role=current_user.role,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset transactions: {str(e)}",
        )

