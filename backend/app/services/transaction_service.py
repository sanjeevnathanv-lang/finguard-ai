import csv
import io
import math
import random
import time
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import func, or_, desc, asc
from sqlalchemy.orm import Session
from app.db.models import (
    Transaction,
    DatasetImport,
    Assessment,
    Case,
    CaseTransaction,
    CaseEvent,
)
from app.services.audit_service import record_audit_event
from app.schemas.transaction import (
    TransactionCreate,
    CSVRowError,
    CSVUploadResponse,
    DashboardMetricsResponse,
    VALID_CURRENCIES,
    VALID_TRANSACTION_TYPES,
    VALID_CHANNELS,
    VALID_STATUSES,
)

MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_CSV_ROWS = 5000
MAX_ERROR_REPORT_ROWS = 50

class DuplicateReferenceError(Exception):
    def __init__(self, reference: str):
        self.reference = reference
        super().__init__(f"Transaction reference '{reference}' already exists.")


class CSVValidationError(Exception):
    def __init__(self, message: str, errors: Optional[List[CSVRowError]] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)


def generate_unique_reference(prefix: str = "TXN") -> str:
    """Generate a clean random transaction reference code."""
    unique_part = uuid.uuid4().hex[:10].upper()
    return f"{prefix}-{unique_part}"


def parse_timestamp_str(ts_str: str) -> datetime:
    """Parse common timestamp string formats and normalize to UTC."""
    ts_str = ts_str.strip()
    # Try ISO formats
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    # Common format fallbacks
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(ts_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date/time format: '{ts_str}'. Expected ISO-8601 or YYYY-MM-DD HH:MM:SS.")


def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Retrieve a single transaction by internal database primary key."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transaction_by_reference(db: Session, reference: str) -> Optional[Transaction]:
    """Retrieve a single transaction by external business reference."""
    return db.query(Transaction).filter(Transaction.reference == reference).first()


def get_transactions_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    currency: Optional[str] = None,
    transaction_type: Optional[str] = None,
    channel: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> Tuple[List[Transaction], int]:
    """Retrieve a paginated, filtered, and sorted list of transactions with stable ordering."""
    query = db.query(Transaction)

    # Search filter across references
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Transaction.reference.ilike(term),
                Transaction.sender_reference.ilike(term),
                Transaction.receiver_reference.ilike(term),
            )
        )

    # Field filters
    if status and status.strip():
        query = query.filter(Transaction.status == status.strip().upper())
    if currency and currency.strip():
        query = query.filter(Transaction.currency == currency.strip().upper())
    if transaction_type and transaction_type.strip():
        query = query.filter(Transaction.transaction_type == transaction_type.strip().upper())
    if channel and channel.strip():
        query = query.filter(Transaction.channel == channel.strip().upper())
    if start_date:
        query = query.filter(Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(Transaction.timestamp <= end_date)

    # Total count after filters
    total = query.count()

    # Determine sort attribute
    sort_column_map = {
        "timestamp": Transaction.timestamp,
        "amount": Transaction.amount,
        "reference": Transaction.reference,
        "currency": Transaction.currency,
        "status": Transaction.status,
        "id": Transaction.id,
    }
    sort_col = sort_column_map.get(sort_by, Transaction.timestamp)

    # Apply stable ordering (secondary key: id)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col), asc(Transaction.id))
    else:
        query = query.order_by(desc(sort_col), desc(Transaction.id))

    # Bounded pagination
    page_size = max(1, min(page_size, 100))
    page = max(1, page)
    offset = (page - 1) * page_size

    items = query.offset(offset).limit(page_size).all()
    return items, total


def create_transaction(
    db: Session,
    data: TransactionCreate,
    provenance: str = "MANUAL_ENTRY",
    is_synthetic: bool = False,
) -> Transaction:
    """Validate and persist a single transaction."""
    ref = data.reference.strip() if data.reference and data.reference.strip() else generate_unique_reference("TXN")

    # Enforce unique business reference
    existing = get_transaction_by_reference(db, ref)
    if existing:
        raise DuplicateReferenceError(ref)

    txn = Transaction(
        reference=ref,
        timestamp=data.timestamp,
        amount=data.amount,
        currency=data.currency,
        sender_reference=data.sender_reference.strip() if data.sender_reference else None,
        receiver_reference=data.receiver_reference.strip() if data.receiver_reference else None,
        transaction_type=data.transaction_type,
        channel=data.channel,
        status=data.status,
        dataset_provenance=provenance,
        is_synthetic=is_synthetic,
        notes=data.notes,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def import_transactions_from_csv(
    db: Session,
    content_bytes: bytes,
    filename: str,
) -> CSVUploadResponse:
    """Validate and ingest transactions from uploaded CSV bytes with atomic batch execution."""
    start_time = time.time()
    import_ref = generate_unique_reference("IMP")

    if len(content_bytes) == 0:
        raise CSVValidationError("The uploaded CSV file is empty.")

    if len(content_bytes) > MAX_CSV_BYTES:
        raise CSVValidationError(
            f"File size exceeds maximum allowed limit of {MAX_CSV_BYTES // (1024*1024)} MB."
        )

    # Decode bytes with encoding fallback
    decoded_text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            decoded_text = content_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise CSVValidationError("Unable to decode CSV file. Please upload a standard UTF-8 encoded file.")

    reader = csv.reader(io.StringIO(decoded_text))
    try:
        header = next(reader, None)
    except Exception as e:
        raise CSVValidationError(f"Malformed CSV format: {str(e)}")

    if not header:
        raise CSVValidationError("CSV file contains no headers or data.")

    # Normalize header column positions
    col_map = {col.strip().lower(): idx for idx, col in enumerate(header)}
    required_cols = {"amount", "transaction_type", "channel"}
    missing_required = required_cols - set(col_map.keys())
    if missing_required:
        raise CSVValidationError(
            f"Missing required columns in CSV: {sorted(list(missing_required))}. "
            f"Found columns: {list(col_map.keys())}"
        )

    row_errors: List[CSVRowError] = []
    transactions_to_insert: List[Transaction] = []
    seen_references_in_file = set()

    total_rows = 0
    row_idx = 1  # 1-indexed, header is row 1, data starts row 2

    for row in reader:
        row_idx += 1
        if not row or all(not cell.strip() for cell in row):
            continue  # skip blank lines

        total_rows += 1
        if total_rows > MAX_CSV_ROWS:
            raise CSVValidationError(f"File exceeds maximum allowed limit of {MAX_CSV_ROWS} data rows.")

        row_has_error = False

        # Extract amount
        amount_idx = col_map["amount"]
        amount_raw = row[amount_idx].strip() if amount_idx < len(row) else ""
        try:
            amount_val = Decimal(amount_raw)
            if math.isnan(amount_val) or math.isinf(amount_val) or amount_val <= 0:
                raise ValueError("Amount must be a positive finite number.")
            amount_val = round(amount_val, 4)
        except (InvalidOperation, ValueError, Exception) as e:
            if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                row_errors.append(CSVRowError(row_number=row_idx, field="amount", error_message=f"Invalid amount '{amount_raw}'"))
            row_has_error = True

        # Extract currency
        currency_raw = "INR"
        if "currency" in col_map and col_map["currency"] < len(row):
            c_val = row[col_map["currency"]].strip().upper()
            if c_val:
                currency_raw = c_val
        if currency_raw not in VALID_CURRENCIES:
            if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                row_errors.append(CSVRowError(row_number=row_idx, field="currency", error_message=f"Unsupported currency '{currency_raw}'"))
            row_has_error = True

        # Extract timestamp
        ts_val = datetime.now(timezone.utc)
        if "timestamp" in col_map and col_map["timestamp"] < len(row):
            ts_raw = row[col_map["timestamp"]].strip()
            if ts_raw:
                try:
                    ts_val = parse_timestamp_str(ts_raw)
                except Exception as e:
                    if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                        row_errors.append(CSVRowError(row_number=row_idx, field="timestamp", error_message=str(e)))
                    row_has_error = True

        # Extract transaction type
        tt_idx = col_map["transaction_type"]
        tt_raw = row[tt_idx].strip().upper() if tt_idx < len(row) else ""
        if tt_raw not in VALID_TRANSACTION_TYPES:
            if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                row_errors.append(CSVRowError(row_number=row_idx, field="transaction_type", error_message=f"Invalid type '{tt_raw}'"))
            row_has_error = True

        # Extract channel
        ch_idx = col_map["channel"]
        ch_raw = row[ch_idx].strip().upper() if ch_idx < len(row) else ""
        if ch_raw not in VALID_CHANNELS:
            if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                row_errors.append(CSVRowError(row_number=row_idx, field="channel", error_message=f"Invalid channel '{ch_raw}'"))
            row_has_error = True

        # Extract reference
        ref_raw = ""
        if "reference" in col_map and col_map["reference"] < len(row):
            ref_raw = row[col_map["reference"]].strip()

        if not ref_raw:
            ref_raw = generate_unique_reference("CSV")
        else:
            # Check duplicate within file
            if ref_raw in seen_references_in_file:
                if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                    row_errors.append(CSVRowError(row_number=row_idx, field="reference", error_message=f"Duplicate reference in file: '{ref_raw}'"))
                row_has_error = True
            seen_references_in_file.add(ref_raw)

            # Check duplicate in database
            if get_transaction_by_reference(db, ref_raw):
                if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                    row_errors.append(CSVRowError(row_number=row_idx, field="reference", error_message=f"Reference already exists in database: '{ref_raw}'"))
                row_has_error = True

        # Optional fields
        sender_val = row[col_map["sender_reference"]].strip() if "sender_reference" in col_map and col_map["sender_reference"] < len(row) else None
        receiver_val = row[col_map["receiver_reference"]].strip() if "receiver_reference" in col_map and col_map["receiver_reference"] < len(row) else None
        status_val = "COMPLETED"
        if "status" in col_map and col_map["status"] < len(row):
            st = row[col_map["status"]].strip().upper()
            if st in VALID_STATUSES:
                status_val = st
            elif st:
                if len(row_errors) < MAX_ERROR_REPORT_ROWS:
                    row_errors.append(CSVRowError(row_number=row_idx, field="status", error_message=f"Invalid status '{st}'"))
                row_has_error = True

        if not row_has_error:
            txn = Transaction(
                reference=ref_raw,
                timestamp=ts_val,
                amount=amount_val,
                currency=currency_raw,
                sender_reference=sender_val or None,
                receiver_reference=receiver_val or None,
                transaction_type=tt_raw,
                channel=ch_raw,
                status=status_val,
                dataset_provenance=f"CSV_IMPORT:{filename}",
                is_synthetic=False,
            )
            transactions_to_insert.append(txn)

    rejected_count = total_rows - len(transactions_to_insert)

    # Perform atomic transactional insert
    try:
        if transactions_to_insert:
            db.bulk_save_objects(transactions_to_insert)

        import_log = DatasetImport(
            import_reference=import_ref,
            filename=filename,
            total_rows=total_rows,
            imported_rows=len(transactions_to_insert),
            skipped_rows=0,
            rejected_rows=rejected_count,
            status="PARTIAL_SUCCESS" if rejected_count > 0 and transactions_to_insert else ("SUCCESS" if not rejected_count else "FAILED"),
        )
        db.add(import_log)
        db.commit()
    except Exception as e:
        db.rollback()
        raise CSVValidationError(f"Database error during CSV import execution: {str(e)}")

    duration_ms = round((time.time() - start_time) * 1000, 2)
    return CSVUploadResponse(
        import_reference=import_ref,
        filename=filename,
        total_rows=total_rows,
        imported_rows=len(transactions_to_insert),
        skipped_rows=0,
        rejected_rows=rejected_count,
        errors=row_errors,
        duration_ms=duration_ms,
        message=f"Processed {total_rows} rows: {len(transactions_to_insert)} imported, {rejected_count} rejected.",
    )


def get_dashboard_metrics(db: Session) -> DashboardMetricsResponse:
    """Compute live dashboard metrics derived strictly from the database."""
    total_txns = db.query(func.count(Transaction.id)).scalar() or 0

    # Status distribution
    status_counts = (
        db.query(Transaction.status, func.count(Transaction.id))
        .group_by(Transaction.status)
        .all()
    )
    status_distribution = {status: count for status, count in status_counts}
    for st in VALID_STATUSES:
        status_distribution.setdefault(st, 0)

    # Volume by currency (avoids aggregating different currencies into a single misleading sum)
    volume_by_curr = (
        db.query(Transaction.currency, func.sum(Transaction.amount))
        .group_by(Transaction.currency)
        .all()
    )
    volume_distribution = {curr: float(vol or 0.0) for curr, vol in volume_by_curr}

    # Recent transactions in the last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.timestamp >= seven_days_ago)
        .scalar()
        or 0
    )

    # Latest transaction timestamp
    latest_ts = db.query(func.max(Transaction.timestamp)).scalar()

    # Dataset provenance summary
    provenance_counts = (
        db.query(Transaction.dataset_provenance, func.count(Transaction.id))
        .group_by(Transaction.dataset_provenance)
        .all()
    )
    dataset_summary = {prov: count for prov, count in provenance_counts}
    synthetic_count = db.query(func.count(Transaction.id)).filter(Transaction.is_synthetic == True).scalar() or 0
    dataset_summary["SYNTHETIC_RECORDS"] = synthetic_count
    dataset_summary["AUTHENTIC_RECORDS"] = total_txns - synthetic_count

    flagged_count = status_distribution.get("FLAGGED", 0)

    return DashboardMetricsResponse(
        total_transactions=total_txns,
        flagged_transactions=flagged_count,
        status_distribution=status_distribution,
        volume_by_currency=volume_distribution,
        recent_transactions_count=recent_count,
        latest_transaction_timestamp=latest_ts,
        dataset_summary=dataset_summary,
        system_health="ok",
    )


def reset_transactions_and_data(
    db: Session,
    actor_username: str = "SYSTEM",
    actor_role: str = "ADMIN",
) -> Dict[str, Any]:
    """Purge all transaction history and operational data while strictly preserving users and audit integrity."""
    # Count rows before deletion
    assessment_count = db.query(func.count(Assessment.id)).scalar() or 0
    case_txn_count = db.query(func.count(CaseTransaction.id)).scalar() or 0
    case_event_count = db.query(func.count(CaseEvent.id)).scalar() or 0
    case_count = db.query(func.count(Case.id)).scalar() or 0
    txn_count = db.query(func.count(Transaction.id)).scalar() or 0
    import_count = db.query(func.count(DatasetImport.id)).scalar() or 0

    # Execute deletion in child-to-parent order to respect foreign key constraints
    db.query(Assessment).delete(synchronize_session=False)
    db.query(CaseTransaction).delete(synchronize_session=False)
    db.query(CaseEvent).delete(synchronize_session=False)
    db.query(Case).delete(synchronize_session=False)
    db.query(Transaction).delete(synchronize_session=False)
    db.query(DatasetImport).delete(synchronize_session=False)

    db.commit()

    # Cryptographically record the purge action into the audit trail
    record_audit_event(
        db,
        event_type="TRANSACTIONS_PURGED",
        actor_username=actor_username,
        actor_role=actor_role,
        record_reference="ALL_TRANSACTIONS",
        status="SUCCESS",
        metadata={
            "transactions_deleted": txn_count,
            "assessments_deleted": assessment_count,
            "cases_deleted": case_count,
            "case_transactions_deleted": case_txn_count,
            "case_events_deleted": case_event_count,
            "dataset_imports_deleted": import_count,
        },
    )

    return {
        "status": "cleared",
        "message": "All transaction history and operational surveillance data have been purged successfully.",
        "transactions_deleted": txn_count,
        "assessments_deleted": assessment_count,
        "cases_deleted": case_count,
        "dataset_imports_deleted": import_count,
    }

