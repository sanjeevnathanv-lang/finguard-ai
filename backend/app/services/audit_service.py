import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def normalize_audit_ts(dt: datetime) -> str:
    """Normalize any datetime (naive or aware) to standard UTC ISO-8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def compute_event_hash(
    event_type: str,
    timestamp_iso: str,
    actor_username: str,
    record_reference: Optional[str],
    status: str,
    metadata_json: Optional[str],
    previous_hash: str,
) -> str:
    """
    Compute deterministic SHA-256 digest of the canonical structured event representation
    chained to the cryptographic hash of the immediate predecessor event.
    """
    canonical_payload = json.dumps(
        {
            "event_type": event_type,
            "timestamp": timestamp_iso,
            "actor_username": actor_username,
            "record_reference": record_reference or "",
            "status": status,
            "metadata_json": metadata_json or "",
            "previous_hash": previous_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def record_audit_event(
    db: Session,
    event_type: str,
    actor_username: str = "SYSTEM",
    actor_role: Optional[str] = None,
    record_reference: Optional[str] = None,
    status: str = "SUCCESS",
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Record an attributable, cryptographically hash-chained audit event.
    Appends to audit_log table without exposing sensitive credentials or secrets.
    """
    now = datetime.now(timezone.utc)
    now_iso = normalize_audit_ts(now)

    # Get hash of the latest event in the chain
    latest_event = (
        db.query(AuditLog.event_hash)
        .order_by(AuditLog.id.desc())
        .first()
    )
    previous_hash = latest_event[0] if latest_event else GENESIS_HASH

    # Sanitize metadata: remove any password or token keys if present
    clean_meta = None
    if metadata:
        clean_meta = {}
        for k, v in metadata.items():
            if any(s in k.lower() for s in ("password", "token", "secret", "hash")):
                clean_meta[k] = "[REDACTED]"
            else:
                clean_meta[k] = v

    meta_json = json.dumps(clean_meta, sort_keys=True) if clean_meta else None

    # Compute hash chain digest
    event_hash = compute_event_hash(
        event_type=event_type,
        timestamp_iso=now_iso,
        actor_username=actor_username,
        record_reference=record_reference,
        status=status,
        metadata_json=meta_json,
        previous_hash=previous_hash,
    )

    audit_entry = AuditLog(
        event_type=event_type,
        timestamp=now,
        actor_username=actor_username,
        actor_role=actor_role,
        record_reference=record_reference,
        status=status,
        ip_address=ip_address,
        metadata_json=meta_json,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )

    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry


def list_audit_logs(
    db: Session,
    event_type: Optional[str] = None,
    actor_username: Optional[str] = None,
    record_reference: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[AuditLog], int]:
    """Retrieve paginated audit log entries ordered by newest first."""
    query = db.query(AuditLog)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if actor_username:
        query = query.filter(AuditLog.actor_username == actor_username)
    if record_reference:
        query = query.filter(AuditLog.record_reference.ilike(f"%{record_reference.strip()}%"))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(desc(AuditLog.id)).offset(offset).limit(page_size).all()
    return items, total


def verify_audit_log_integrity(db: Session) -> Dict[str, Any]:
    """
    Cryptographic verification of the audit log hash chain.
    Walks from genesis through every historical record verifying:
      1. previous_hash matches the prior event's computed event_hash.
      2. event_hash matches SHA-256 of canonical event contents + previous_hash.
    Reports verification status, verified count, and index of any corrupted or tampered record.

    SECURITY NOTE:
    While this cryptographic hash chain detects inadvertent corruption, out-of-order deletion,
    or unauthorized single-row modifications, a privileged administrator with direct physical write
    access to the SQLite database file on disk could recompute the entire chain.
    Absolute immutability requires external append-only write-once-read-many (WORM) storage.
    """
    records = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not records:
        return {
            "is_valid": True,
            "total_records_checked": 0,
            "status": "EMPTY_CHAIN",
            "message": "No audit records present in database.",
            "tampered_record_id": None,
        }

    expected_prev = GENESIS_HASH
    for idx, r in enumerate(records):
        # 1. Check previous_hash link
        if r.previous_hash != expected_prev:
            return {
                "is_valid": False,
                "total_records_checked": idx,
                "status": "BROKEN_LINK",
                "tampered_record_id": r.id,
                "message": f"Broken hash chain at record ID {r.id}. Expected previous_hash {expected_prev}, found {r.previous_hash}.",
            }

        # 2. Check event_hash
        ts_iso = normalize_audit_ts(r.timestamp) if r.timestamp else ""
        expected_hash = compute_event_hash(
            event_type=r.event_type,
            timestamp_iso=ts_iso,
            actor_username=r.actor_username,
            record_reference=r.record_reference,
            status=r.status,
            metadata_json=r.metadata_json,
            previous_hash=expected_prev,
        )

        if r.event_hash != expected_hash:
            return {
                "is_valid": False,
                "total_records_checked": idx,
                "status": "HASH_MISMATCH",
                "tampered_record_id": r.id,
                "message": f"Hash mismatch at record ID {r.id}. Stored hash does not match canonical recomputed digest.",
            }

        expected_prev = r.event_hash

    return {
        "is_valid": True,
        "total_records_checked": len(records),
        "status": "VERIFIED_VALID",
        "latest_hash": expected_prev,
        "message": f"Successfully verified integrity of all {len(records)} audit log records.",
        "tampered_record_id": None,
    }
