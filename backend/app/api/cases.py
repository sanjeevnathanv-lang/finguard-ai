import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Case, Assessment, Transaction
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseCloseRequest,
    CaseNoteCreate,
    CaseTransactionLinkRequest,
    CaseRead,
    CaseListResponse,
    CaseTransactionRead,
    TimelineEventRead,
    RelatedTransactionRead,
    CaseExportResponse,
)
from app.services import case_service, related_analysis_service, timeline_service
from app.services.case_service import (
    CaseNotFoundError,
    TransactionAlreadyLinkedError,
    InvalidCaseStatusTransitionError,
)
from app.services.assessment_service import TransactionNotFoundError
from app.core.deps import require_analyst, require_viewer
from app.db.models import User
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/cases", tags=["cases"])


def format_case_read(db: Session, case: Case, include_details: bool = False) -> CaseRead:
    """Format SQLAlchemy Case model into CaseRead DTO with linked transaction assessment enrichment."""
    transactions_count = len(case.transactions)
    events_count = len(case.events)

    txn_dtos = None
    event_dtos = None

    if include_details:
        txn_dtos = []
        for link in case.transactions:
            t: Transaction = link.transaction
            latest_asmt = (
                db.query(Assessment)
                .filter(Assessment.transaction_id == t.id)
                .order_by(Assessment.created_at.desc())
                .first()
            )
            asmt_data = None
            if latest_asmt:
                asmt_data = {
                    "id": latest_asmt.id,
                    "final_recommendation": latest_asmt.final_recommendation,
                    "overall_severity": latest_asmt.overall_severity,
                    "risk_score": float(latest_asmt.risk_score),
                    "rules_triggered_count": latest_asmt.rules_triggered_count,
                    "engine_version": latest_asmt.engine_version,
                    "model_version": latest_asmt.model_version,
                    "created_at": latest_asmt.created_at.isoformat(),
                }

            txn_dtos.append(
                CaseTransactionRead(
                    id=link.id,
                    transaction_id=t.id,
                    transaction_reference=t.reference,
                    timestamp=t.timestamp,
                    amount=t.amount,
                    currency=t.currency,
                    transaction_type=t.transaction_type,
                    channel=t.channel,
                    status=t.status,
                    sender_reference=t.sender_reference,
                    receiver_reference=t.receiver_reference,
                    linking_reason=link.linking_reason,
                    linked_at=link.linked_at,
                    latest_assessment=asmt_data,
                )
            )

        event_dtos = []
        for ev in case.events:
            meta = None
            if ev.metadata_json:
                try:
                    meta = json.loads(ev.metadata_json)
                except Exception:
                    meta = {"raw": ev.metadata_json}
            event_dtos.append(
                TimelineEventRead(
                    id=ev.id,
                    case_id=case.id,
                    event_type=ev.event_type,
                    title=ev.title,
                    description=ev.description,
                    source=ev.source,
                    actor=ev.actor,
                    event_timestamp=ev.event_timestamp,
                    metadata=meta,
                )
            )

    return CaseRead(
        id=case.id,
        case_reference=case.case_reference,
        title=case.title,
        summary=case.summary,
        status=case.status,
        priority=case.priority,
        assigned_reviewer=case.assigned_reviewer,
        reviewer_notes=case.reviewer_notes,
        final_disposition=case.final_disposition,
        disposition_notes=case.disposition_notes,
        closed_at=case.closed_at,
        created_at=case.created_at,
        updated_at=case.updated_at,
        linked_transactions_count=transactions_count,
        events_count=events_count,
        transactions=txn_dtos,
        events=event_dtos,
    )


@router.get("", response_model=CaseListResponse)
def list_cases_endpoint(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, IN_REVIEW, WAITING_FOR_INFORMATION, CLOSED)"),
    priority: Optional[str] = Query(None, description="Filter by review priority (LOW, MEDIUM, HIGH, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search by reference, title, summary, or assigned reviewer"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve paginated investigation cases with status/priority filtering and keyword search."""
    cases, total = case_service.list_cases(
        db, status=status, priority=priority, search=search, page=page, page_size=page_size
    )
    items = [format_case_read(db, c, include_details=False) for c in cases]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return CaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(
    case_in: CaseCreate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Create a new investigation case, optionally linking initial transactions and opening reviewer notes."""
    if not case_in.assigned_reviewer:
        case_in.assigned_reviewer = current_user.username
    case = case_service.create_case(db, case_in)
    record_audit_event(
        db,
        event_type="CASE_CREATED",
        actor_username=current_user.username,
        actor_role=current_user.role,
        record_reference=case.case_reference,
        status="SUCCESS",
        metadata={"case_id": case.id, "priority": case.priority},
    )
    return format_case_read(db, case, include_details=True)


@router.get("/{case_id}", response_model=CaseRead)
def get_case_endpoint(
    case_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve full investigation case details including linked transactions and audit event log."""
    case = case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
    return format_case_read(db, case, include_details=True)


@router.patch("/{case_id}", response_model=CaseRead)
def update_case_endpoint(
    case_id: int,
    case_in: CaseUpdate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Update investigation case fields, validating status transitions."""
    try:
        case = case_service.update_case(db, case_id, case_in)
        record_audit_event(
            db,
            event_type="CASE_UPDATED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=case.case_reference,
            status="SUCCESS",
            metadata={"status": case.status, "priority": case.priority},
        )
        return format_case_read(db, case, include_details=True)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
    except InvalidCaseStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{case_id}/transactions", response_model=CaseRead)
def link_transaction_endpoint(
    case_id: int,
    link_in: CaseTransactionLinkRequest,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Link a transaction to the investigation case with an investigator rationale."""
    try:
        case_service.link_transaction(db, case_id, link_in)
        case = case_service.get_case(db, case_id)
        record_audit_event(
            db,
            event_type="CASE_TRANSACTION_LINKED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=case.case_reference,
            status="SUCCESS",
            metadata={"transaction_id": link_in.transaction_id},
        )
        return format_case_read(db, case, include_details=True)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
    except TransactionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction with ID {link_in.transaction_id} not found.")
    except TransactionAlreadyLinkedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{case_id}/transactions/{transaction_id}", response_model=CaseRead)
def unlink_transaction_endpoint(
    case_id: int,
    transaction_id: int,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Unlink a transaction from the investigation case."""
    try:
        case = case_service.get_case(db, case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
        removed = case_service.unlink_transaction(db, case_id, transaction_id)
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction {transaction_id} is not linked to case {case_id}.")
        record_audit_event(
            db,
            event_type="CASE_TRANSACTION_UNLINKED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=case.case_reference,
            status="SUCCESS",
            metadata={"transaction_id": transaction_id},
        )
        return format_case_read(db, case, include_details=True)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")


@router.post("/{case_id}/notes", response_model=TimelineEventRead)
def add_reviewer_note_endpoint(
    case_id: int,
    note_in: CaseNoteCreate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Add an investigator note to the case and record it on the case audit timeline."""
    if not note_in.author or note_in.author == "Reviewer":
        note_in.author = current_user.username
    try:
        event = case_service.add_reviewer_note(db, case_id, note_in)
        case = case_service.get_case(db, case_id)
        record_audit_event(
            db,
            event_type="CASE_NOTE_ADDED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=case.case_reference if case else f"Case {case_id}",
            status="SUCCESS",
        )
        return TimelineEventRead(
            id=event.id,
            case_id=case_id,
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            source=event.source,
            actor=event.actor,
            event_timestamp=event.event_timestamp,
        )
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")


@router.post("/{case_id}/close", response_model=CaseRead)
def close_case_endpoint(
    case_id: int,
    close_in: CaseCloseRequest,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """
    Close an investigation case by recording a final reviewer disposition:
    UNVERIFIED_SUSPICION, CONFIRMED_LEGITIMATE, CONFIRMED_FRAUD, or INCONCLUSIVE,
    accompanied by mandatory rationale.
    """
    if not close_in.reviewer_name:
        close_in.reviewer_name = current_user.username
    try:
        case = case_service.close_case(db, case_id, close_in)
        record_audit_event(
            db,
            event_type="CASE_CLOSED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=case.case_reference,
            status="SUCCESS",
            metadata={"disposition": case.final_disposition},
        )
        return format_case_read(db, case, include_details=True)
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
    except InvalidCaseStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{case_id}/timeline", response_model=List[TimelineEventRead])
def get_case_timeline_endpoint(
    case_id: int,
    ascending: bool = Query(True, description="Sort chronologically (True) or reverse (False)"),
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """
    Retrieve the multi-source unified evidence timeline merging:
    - Case lifecycle events
    - Reviewer notes
    - Transaction execution timestamps
    - AI Expert system & ML assessment traces
    """
    case = case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
    return timeline_service.get_case_timeline(db, case_id, ascending=ascending)


@router.get("/{case_id}/related-transactions", response_model=List[RelatedTransactionRead])
def get_related_transactions_endpoint(
    case_id: int,
    max_results: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """
    Perform explainable relational analysis against database transactions to identify
    shared senders, receivers, or temporal clustering relative to this case's scope.
    """
    case = case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
    return related_analysis_service.find_related_transactions(db, case_id, max_results=max_results)


@router.get("/{case_id}/export", response_model=CaseExportResponse)
def export_case_summary_endpoint(
    case_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """
    Generate an exportable comprehensive case report in structured Markdown and JSON,
    with spreadsheet formula injection safeguards.
    """
    try:
        res = case_service.export_case_summary(db, case_id)
        record_audit_event(
            db,
            event_type="CASE_REPORT_EXPORTED",
            actor_username=current_user.username,
            actor_role=current_user.role,
            record_reference=res.case_reference,
            status="SUCCESS",
        )
        return res
    except CaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID {case_id} not found.")
