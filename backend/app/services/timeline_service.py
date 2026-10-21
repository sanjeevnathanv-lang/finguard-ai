import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Case, CaseEvent, CaseTransaction, Transaction, Assessment
from app.schemas.case import TimelineEventRead


def get_case_timeline(
    db: Session,
    case_id: int,
    ascending: bool = True,
) -> List[TimelineEventRead]:
    """
    Compile a unified chronological multi-source evidence timeline for an investigation case.
    Merges:
      1. Direct case lifecycle events and reviewer notes (CaseEvent).
      2. Transaction creation timestamps for linked transactions.
      3. Assessment events and inference traces for linked transactions.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return []

    timeline_items: List[Dict[str, Any]] = []

    # 1. Pull direct case events
    direct_events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).all()
    for ev in direct_events:
        meta = None
        if ev.metadata_json:
            try:
                meta = json.loads(ev.metadata_json)
            except Exception:
                meta = {"raw": ev.metadata_json}

        timeline_items.append({
            "id": ev.id,
            "case_id": case.id,
            "event_type": ev.event_type,
            "title": ev.title,
            "description": ev.description,
            "source": ev.source,
            "actor": ev.actor,
            "event_timestamp": ev.event_timestamp,
            "metadata": meta,
        })

    # 2. Pull linked transactions & their assessments
    links = db.query(CaseTransaction).filter(CaseTransaction.case_id == case_id).all()
    for link in links:
        t: Transaction = link.transaction
        if t:
            # Transaction original timestamp event
            timeline_items.append({
                "id": -abs(t.id * 1000 + 1),  # deterministic synthetic ID for non-case_event records
                "case_id": case.id,
                "event_type": "TRANSACTION_OCCURRED",
                "title": f"Transaction {t.reference} Executed",
                "description": f"{t.channel} {t.transaction_type} of {t.amount:.2f} {t.currency} (Status: {t.status})",
                "source": "TRANSACTION_LEDGER",
                "actor": t.sender_reference or "Counterparty",
                "event_timestamp": t.timestamp,
                "metadata": {
                    "transaction_id": t.id,
                    "reference": t.reference,
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "channel": t.channel,
                    "status": t.status,
                    "sender": t.sender_reference,
                    "receiver": t.receiver_reference,
                },
            })

            # Pull assessments for this transaction
            assessments = (
                db.query(Assessment)
                .filter(Assessment.transaction_id == t.id)
                .order_by(Assessment.created_at.asc())
                .all()
            )
            for idx, asmt in enumerate(assessments):
                rules_summary = f"{asmt.rules_triggered_count} rule(s) triggered"
                hybrid_desc = (
                    f"Hybrid AI evaluation: {asmt.final_recommendation} "
                    f"(Severity: {asmt.overall_severity}, Risk Score: {asmt.risk_score:.1f}/100, {rules_summary})"
                )
                timeline_items.append({
                    "id": -abs(t.id * 1000 + 10 + idx),
                    "case_id": case.id,
                    "event_type": "ASSESSMENT_PERFORMED",
                    "title": f"AI Risk Assessment: {t.reference}",
                    "description": hybrid_desc,
                    "source": "AI_EXPERT_SYSTEM",
                    "actor": f"Engine v{asmt.engine_version}",
                    "event_timestamp": asmt.created_at,
                    "metadata": {
                        "assessment_id": asmt.id,
                        "transaction_id": t.id,
                        "transaction_reference": t.reference,
                        "recommendation": asmt.final_recommendation,
                        "severity": asmt.overall_severity,
                        "risk_score": float(asmt.risk_score),
                        "rules_triggered_count": asmt.rules_triggered_count,
                        "model_version": asmt.model_version,
                    },
                })

    # Sort timeline by event_timestamp
    def get_sort_key(item):
        ts = item["event_timestamp"]
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts

    timeline_items.sort(key=get_sort_key, reverse=not ascending)

    return [TimelineEventRead(**item) for item in timeline_items]
