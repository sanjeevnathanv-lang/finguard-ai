import json
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.db.models import Case, CaseTransaction, CaseEvent, Transaction, Assessment
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseCloseRequest,
    CaseNoteCreate,
    CaseTransactionLinkRequest,
    VALID_STATUS_TRANSITIONS,
    VALID_DISPOSITIONS,
    VALID_CASE_STATUSES,
    CaseExportResponse,
)


class CaseNotFoundError(Exception):
    def __init__(self, case_id: int):
        self.case_id = case_id
        super().__init__(f"Case with ID {case_id} does not exist.")


class TransactionAlreadyLinkedError(Exception):
    def __init__(self, case_id: int, transaction_id: int):
        self.case_id = case_id
        self.transaction_id = transaction_id
        super().__init__(f"Transaction {transaction_id} is already linked to case {case_id}.")


class InvalidCaseStatusTransitionError(Exception):
    def __init__(self, from_status: str, to_status: str, reason: str = ""):
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        super().__init__(
            f"Invalid status transition from '{from_status}' to '{to_status}'."
            + (f" Reason: {reason}" if reason else "")
        )


def sanitize_export_text(val: Any) -> str:
    """Sanitize strings against formula injection when exporting to CSV/Text/Markdown."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def generate_case_reference(db: Session) -> str:
    """Generate a collision-resistant, readable case reference like CASE-20261021-A1B2."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(10):
        token = secrets.token_hex(2).upper()
        ref = f"CASE-{date_part}-{token}"
        existing = db.query(Case.id).filter(Case.case_reference == ref).first()
        if not existing:
            return ref
    # Fallback with timestamp
    ts_hex = hex(int(datetime.now(timezone.utc).timestamp()))[2:].upper()
    return f"CASE-{date_part}-{ts_hex}"


def create_case(db: Session, case_in: CaseCreate) -> Case:
    """Create a new investigation case with audit log and optional initial transactions."""
    ref = generate_case_reference(db)
    now = datetime.now(timezone.utc)

    case = Case(
        case_reference=ref,
        title=case_in.title,
        summary=case_in.summary,
        status="OPEN",
        priority=case_in.priority,
        assigned_reviewer=case_in.assigned_reviewer,
        created_at=now,
        updated_at=now,
    )
    db.add(case)
    db.flush()

    # Initial system creation event
    create_event = CaseEvent(
        case_id=case.id,
        event_type="CASE_CREATED",
        title="Case Opened",
        description=f"Investigation case opened with review priority {case.priority}.",
        source="SYSTEM",
        actor="System",
        event_timestamp=now,
        metadata_json=json.dumps({"priority": case.priority, "reference": ref}),
    )
    db.add(create_event)

    # Initial investigator note if provided
    if case_in.initial_note:
        case.reviewer_notes = f"[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {case_in.assigned_reviewer or 'Reviewer'}: {case_in.initial_note}"
        note_event = CaseEvent(
            case_id=case.id,
            event_type="REVIEWER_NOTE",
            title="Initial Reviewer Note",
            description=case_in.initial_note,
            source="REVIEWER",
            actor=case_in.assigned_reviewer or "Reviewer",
            event_timestamp=now,
        )
        db.add(note_event)

    # Link initial transactions if provided
    if case_in.initial_transaction_ids:
        for tid in case_in.initial_transaction_ids:
            txn = db.query(Transaction).filter(Transaction.id == tid).first()
            if txn:
                link = CaseTransaction(
                    case_id=case.id,
                    transaction_id=txn.id,
                    linking_reason=case_in.linking_reason or "Linked on case creation",
                    linked_at=now,
                )
                db.add(link)

                link_event = CaseEvent(
                    case_id=case.id,
                    event_type="TRANSACTION_LINKED",
                    title=f"Transaction {txn.reference} Linked",
                    description=case_in.linking_reason or "Linked on case creation",
                    source="SYSTEM",
                    actor="System",
                    event_timestamp=now,
                    metadata_json=json.dumps({
                        "transaction_id": txn.id,
                        "reference": txn.reference,
                        "amount": float(txn.amount),
                        "currency": txn.currency,
                    }),
                )
                db.add(link_event)

    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> Optional[Case]:
    """Retrieve case by ID."""
    return db.query(Case).filter(Case.id == case_id).first()


def list_cases(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Case], int]:
    """Query cases with optional filtering, search, and pagination."""
    query = db.query(Case)

    if status:
        query = query.filter(Case.status == status.upper())
    if priority:
        query = query.filter(Case.priority == priority.upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Case.case_reference.ilike(s),
                Case.title.ilike(s),
                Case.summary.ilike(s),
                Case.assigned_reviewer.ilike(s),
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(desc(Case.created_at)).offset(offset).limit(page_size).all()
    return items, total


def update_case(db: Session, case_id: int, case_in: CaseUpdate) -> Case:
    """Update case details, validate status transitions, and record audit events."""
    case = get_case(db, case_id)
    if not case:
        raise CaseNotFoundError(case_id)

    now = datetime.now(timezone.utc)

    # Validate status transition if requested
    if case_in.status and case_in.status != case.status:
        target_status = case_in.status.upper()
        if target_status not in VALID_CASE_STATUSES:
            raise InvalidCaseStatusTransitionError(case.status, target_status, "Unknown status value")

        allowed = VALID_STATUS_TRANSITIONS.get(case.status, set())
        if target_status not in allowed:
            raise InvalidCaseStatusTransitionError(
                case.status,
                target_status,
                f"Transition from {case.status} to {target_status} is not allowed."
            )

        if target_status == "CLOSED":
            raise InvalidCaseStatusTransitionError(
                case.status,
                "CLOSED",
                "Cases cannot be closed directly via update. Use the dedicated /close endpoint to supply a mandatory disposition and rationale."
            )

        old_status = case.status
        case.status = target_status

        # If reopening from closed, reset closed_at
        if old_status == "CLOSED" and target_status in ("OPEN", "IN_REVIEW"):
            case.closed_at = None
            event_type = "CASE_REOPENED"
            title = f"Case Reopened: {target_status}"
        else:
            event_type = "STATUS_UPDATED"
            title = f"Status Changed to {target_status}"

        db.add(CaseEvent(
            case_id=case.id,
            event_type=event_type,
            title=title,
            description=f"Status changed from {old_status} to {target_status}.",
            source="REVIEWER",
            actor=case.assigned_reviewer or "Reviewer",
            event_timestamp=now,
            metadata_json=json.dumps({"old_status": old_status, "new_status": target_status}),
        ))

    if case_in.title is not None:
        case.title = case_in.title
    if case_in.summary is not None:
        case.summary = case_in.summary
    if case_in.priority is not None and case_in.priority != case.priority:
        old_priority = case.priority
        case.priority = case_in.priority
        db.add(CaseEvent(
            case_id=case.id,
            event_type="PRIORITY_CHANGED",
            title=f"Review Priority set to {case.priority}",
            description=f"Priority modified from {old_priority} to {case.priority}.",
            source="REVIEWER",
            actor=case.assigned_reviewer or "Reviewer",
            event_timestamp=now,
        ))

    if case_in.assigned_reviewer is not None and case_in.assigned_reviewer != case.assigned_reviewer:
        old_rev = case.assigned_reviewer
        case.assigned_reviewer = case_in.assigned_reviewer
        db.add(CaseEvent(
            case_id=case.id,
            event_type="ASSIGNEE_CHANGED",
            title=f"Assigned to {case.assigned_reviewer}",
            description=f"Reviewer reassigned from '{old_rev or 'Unassigned'}' to '{case.assigned_reviewer}'.",
            source="REVIEWER",
            actor=case.assigned_reviewer,
            event_timestamp=now,
        ))

    if case_in.reviewer_notes is not None:
        case.reviewer_notes = case_in.reviewer_notes

    case.updated_at = now
    db.commit()
    db.refresh(case)
    return case


def link_transaction(db: Session, case_id: int, link_in: CaseTransactionLinkRequest) -> CaseTransaction:
    """Link a transaction to an investigation case."""
    case = get_case(db, case_id)
    if not case:
        raise CaseNotFoundError(case_id)

    txn = db.query(Transaction).filter(Transaction.id == link_in.transaction_id).first()
    if not txn:
        from app.services.assessment_service import TransactionNotFoundError
        raise TransactionNotFoundError(link_in.transaction_id)

    # Check if already linked
    existing = (
        db.query(CaseTransaction)
        .filter(CaseTransaction.case_id == case_id, CaseTransaction.transaction_id == txn.id)
        .first()
    )
    if existing:
        raise TransactionAlreadyLinkedError(case_id, txn.id)

    now = datetime.now(timezone.utc)
    link = CaseTransaction(
        case_id=case.id,
        transaction_id=txn.id,
        linking_reason=link_in.linking_reason or "Manually linked by reviewer",
        linked_at=now,
    )
    db.add(link)

    event = CaseEvent(
        case_id=case.id,
        event_type="TRANSACTION_LINKED",
        title=f"Transaction {txn.reference} Linked",
        description=link_in.linking_reason or "Manually linked by reviewer",
        source="REVIEWER",
        actor=case.assigned_reviewer or "Reviewer",
        event_timestamp=now,
        metadata_json=json.dumps({
            "transaction_id": txn.id,
            "reference": txn.reference,
            "amount": float(txn.amount),
            "currency": txn.currency,
            "channel": txn.channel,
        }),
    )
    db.add(event)

    case.updated_at = now
    db.commit()
    db.refresh(link)
    return link


def unlink_transaction(db: Session, case_id: int, transaction_id: int) -> bool:
    """Remove a linked transaction from an investigation case."""
    case = get_case(db, case_id)
    if not case:
        raise CaseNotFoundError(case_id)

    link = (
        db.query(CaseTransaction)
        .filter(CaseTransaction.case_id == case_id, CaseTransaction.transaction_id == transaction_id)
        .first()
    )
    if not link:
        return False

    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    txn_ref = txn.reference if txn else f"ID {transaction_id}"

    db.delete(link)
    now = datetime.now(timezone.utc)

    event = CaseEvent(
        case_id=case.id,
        event_type="TRANSACTION_UNLINKED",
        title=f"Transaction {txn_ref} Unlinked",
        description="Transaction removed from case scope.",
        source="REVIEWER",
        actor=case.assigned_reviewer or "Reviewer",
        event_timestamp=now,
        metadata_json=json.dumps({"transaction_id": transaction_id, "reference": txn_ref}),
    )
    db.add(event)
    case.updated_at = now
    db.commit()
    return True


def add_reviewer_note(db: Session, case_id: int, note_in: CaseNoteCreate) -> CaseEvent:
    """Append a timestamped reviewer note and timeline event to the case."""
    case = get_case(db, case_id)
    if not case:
        raise CaseNotFoundError(case_id)

    now = datetime.now(timezone.utc)
    author = note_in.author or case.assigned_reviewer or "Reviewer"
    stamp = f"[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {author}: {note_in.note}"

    if case.reviewer_notes:
        case.reviewer_notes = f"{case.reviewer_notes}\n\n{stamp}"
    else:
        case.reviewer_notes = stamp

    event = CaseEvent(
        case_id=case.id,
        event_type="REVIEWER_NOTE",
        title=f"Note from {author}",
        description=note_in.note,
        source="REVIEWER",
        actor=author,
        event_timestamp=now,
    )
    db.add(event)
    case.updated_at = now
    db.commit()
    db.refresh(event)
    return event


def close_case(db: Session, case_id: int, close_in: CaseCloseRequest) -> Case:
    """Close an investigation case with mandatory reviewer disposition and audit rationale."""
    case = get_case(db, case_id)
    if not case:
        raise CaseNotFoundError(case_id)

    if case.status == "CLOSED":
        raise InvalidCaseStatusTransitionError("CLOSED", "CLOSED", "Case is already closed.")

    now = datetime.now(timezone.utc)
    actor = close_in.reviewer_name or case.assigned_reviewer or "Reviewer"

    case.status = "CLOSED"
    case.final_disposition = close_in.final_disposition
    case.disposition_notes = close_in.disposition_notes
    case.closed_at = now
    case.updated_at = now
    if not case.assigned_reviewer and close_in.reviewer_name:
        case.assigned_reviewer = close_in.reviewer_name

    event = CaseEvent(
        case_id=case.id,
        event_type="CASE_CLOSED",
        title=f"Case Closed: {case.final_disposition}",
        description=close_in.disposition_notes,
        source="REVIEWER",
        actor=actor,
        event_timestamp=now,
        metadata_json=json.dumps({
            "disposition": case.final_disposition,
            "disposition_notes": case.disposition_notes,
            "closed_at": now.isoformat(),
        }),
    )
    db.add(event)
    db.commit()
    db.refresh(case)
    return case


def export_case_summary(db: Session, case_id: int) -> CaseExportResponse:
    """Compile comprehensive investigation summary with sanitized fields to avoid formula injection."""
    case = get_case(db, case_id)
    if not case:
        raise CaseNotFoundError(case_id)

    now = datetime.now(timezone.utc)
    linked_txns = case.transactions
    events = case.events

    # Pull latest assessment for each linked transaction
    txn_summaries = []
    for link in linked_txns:
        t = link.transaction
        latest_assessment = (
            db.query(Assessment)
            .filter(Assessment.transaction_id == t.id)
            .order_by(Assessment.created_at.desc())
            .first()
        )
        asmt_info = None
        if latest_assessment:
            asmt_info = {
                "recommendation": sanitize_export_text(latest_assessment.final_recommendation),
                "severity": sanitize_export_text(latest_assessment.overall_severity),
                "risk_score": float(latest_assessment.risk_score),
                "rules_triggered": latest_assessment.rules_triggered_count,
            }

        txn_summaries.append({
            "id": t.id,
            "reference": sanitize_export_text(t.reference),
            "amount": float(t.amount),
            "currency": sanitize_export_text(t.currency),
            "channel": sanitize_export_text(t.channel),
            "timestamp": t.timestamp.isoformat(),
            "status": sanitize_export_text(t.status),
            "sender_reference": sanitize_export_text(t.sender_reference),
            "receiver_reference": sanitize_export_text(t.receiver_reference),
            "linking_reason": sanitize_export_text(link.linking_reason),
            "linked_at": link.linked_at.isoformat(),
            "latest_assessment": asmt_info,
        })

    event_summaries = []
    for ev in events:
        event_summaries.append({
            "timestamp": ev.event_timestamp.isoformat(),
            "type": sanitize_export_text(ev.event_type),
            "title": sanitize_export_text(ev.title),
            "description": sanitize_export_text(ev.description),
            "source": sanitize_export_text(ev.source),
            "actor": sanitize_export_text(ev.actor),
        })

    # Build executive summary
    status_label = f"Status: {case.status} (Review Priority: {case.priority})"
    disposition_label = (
        f"Disposition: {case.final_disposition} (Closed at {case.closed_at.isoformat()})"
        if case.status == "CLOSED" and case.closed_at
        else "Investigation active (no final disposition reached)"
    )
    exec_summary = (
        f"FinGuard AI Case Audit Summary for {case.case_reference} — '{case.title}'.\n"
        f"{status_label}. {disposition_label}.\n"
        f"Assigned Reviewer: {case.assigned_reviewer or 'Unassigned'}.\n"
        f"Linked Transactions: {len(linked_txns)} | Timeline Audit Events: {len(events)}."
    )

    # Build Markdown report
    md_lines = [
        f"# FinGuard AI Investigation Report — {sanitize_export_text(case.case_reference)}",
        f"**Title**: {sanitize_export_text(case.title)}  ",
        f"**Review Priority**: {sanitize_export_text(case.priority)} (Review triage level, not confirmed fraud severity)  ",
        f"**Current Status**: {sanitize_export_text(case.status)}  ",
        f"**Assigned Reviewer**: {sanitize_export_text(case.assigned_reviewer or 'Unassigned')}  ",
        f"**Created At**: {case.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
    ]
    if case.closed_at:
        md_lines.append(f"**Closed At**: {case.closed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
        md_lines.append(f"**Final Disposition**: {sanitize_export_text(case.final_disposition)}  ")
        md_lines.append(f"**Disposition Rationale**: {sanitize_export_text(case.disposition_notes)}  ")

    md_lines.append("\n## Executive Summary")
    md_lines.append(sanitize_export_text(case.summary or 'No initial summary recorded.'))

    md_lines.append("\n## Scope: Linked Transactions")
    if not txn_summaries:
        md_lines.append("_No transactions currently linked to this case._")
    else:
        md_lines.append("| Reference | Timestamp | Amount | Channel | Status | Latest Risk Score | Recommendation | Linking Reason |")
        md_lines.append("|---|---|---|---|---|---|---|---|")
        for ts in txn_summaries:
            asmt = ts["latest_assessment"]
            score_str = f"{asmt['risk_score']:.1f}/100" if asmt else "Unassessed"
            rec_str = asmt["recommendation"] if asmt else "N/A"
            md_lines.append(
                f"| {ts['reference']} | {ts['timestamp'][:19]} | {ts['amount']:.2f} {ts['currency']} | {ts['channel']} | {ts['status']} | {score_str} | {rec_str} | {ts['linking_reason']} |"
            )

    md_lines.append("\n## Investigator Review Notes")
    if case.reviewer_notes:
        md_lines.append(sanitize_export_text(case.reviewer_notes))
    else:
        md_lines.append("_No reviewer notes entered._")

    md_lines.append("\n## Multi-Source Evidence Timeline")
    for ev in event_summaries:
        md_lines.append(
            f"- **{ev['timestamp'][:19]} UTC** [{ev['source']}] **{ev['title']}** ({ev['actor'] or 'System'}): {ev['description'] or ''}"
        )

    md_report = "\n".join(md_lines)

    report_json = {
        "case_reference": sanitize_export_text(case.case_reference),
        "title": sanitize_export_text(case.title),
        "summary": sanitize_export_text(case.summary),
        "status": sanitize_export_text(case.status),
        "priority": sanitize_export_text(case.priority),
        "assigned_reviewer": sanitize_export_text(case.assigned_reviewer),
        "final_disposition": sanitize_export_text(case.final_disposition),
        "disposition_notes": sanitize_export_text(case.disposition_notes),
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "linked_transactions": txn_summaries,
        "timeline_events": event_summaries,
    }

    return CaseExportResponse(
        case_reference=sanitize_export_text(case.case_reference),
        title=sanitize_export_text(case.title),
        status=case.status,
        priority=case.priority,
        assigned_reviewer=sanitize_export_text(case.assigned_reviewer),
        created_at=case.created_at,
        closed_at=case.closed_at,
        final_disposition=sanitize_export_text(case.final_disposition),
        disposition_notes=sanitize_export_text(case.disposition_notes),
        total_linked_transactions=len(linked_txns),
        total_timeline_events=len(events),
        executive_summary=exec_summary,
        report_markdown=md_report,
        report_json=report_json,
    )
