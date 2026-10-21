from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Boolean,
    Index,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reference = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    amount = Column(Numeric(precision=18, scale=4), nullable=False)
    currency = Column(String(3), index=True, nullable=False, default="INR")
    sender_reference = Column(String(128), index=True, nullable=True)
    receiver_reference = Column(String(128), index=True, nullable=True)
    transaction_type = Column(String(32), index=True, nullable=False)
    channel = Column(String(32), index=True, nullable=False)
    status = Column(String(32), index=True, nullable=False, default="COMPLETED")
    dataset_provenance = Column(String(64), nullable=False, default="MANUAL")
    is_synthetic = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("ix_transactions_timestamp_id", "timestamp", "id"),
        Index("ix_transactions_currency_status", "currency", "status"),
        Index("ix_transactions_channel_type", "channel", "transaction_type"),
    )


class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    import_reference = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, nullable=False, default=0)
    imported_rows = Column(Integer, nullable=False, default=0)
    skipped_rows = Column(Integer, nullable=False, default=0)
    rejected_rows = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="SUCCESS")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_reference = Column(String(64), index=True, nullable=True)
    final_recommendation = Column(String(64), index=True, nullable=False)
    overall_severity = Column(String(32), index=True, nullable=False)
    risk_score = Column(Numeric(precision=5, scale=2), nullable=False)
    rules_triggered_count = Column(Integer, nullable=False, default=0)
    engine_version = Column(String(32), nullable=False)
    knowledge_base_version = Column(String(32), nullable=False)
    model_version = Column(String(32), nullable=True)
    trace_json = Column(Text, nullable=False)
    hybrid_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_assessments_txn_created", "transaction_id", "created_at"),
        Index("ix_assessments_rec_sev", "final_recommendation", "overall_severity"),
    )


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_reference = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String(32), index=True, nullable=False, default="OPEN")  # OPEN, IN_REVIEW, WAITING_FOR_INFORMATION, CLOSED
    priority = Column(String(32), index=True, nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    assigned_reviewer = Column(String(128), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    final_disposition = Column(String(64), nullable=True)  # UNVERIFIED_SUSPICION, CONFIRMED_LEGITIMATE, CONFIRMED_FRAUD, INCONCLUSIVE
    disposition_notes = Column(Text, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    transactions = relationship("CaseTransaction", back_populates="case", cascade="all, delete-orphan")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan", order_by="CaseEvent.event_timestamp.asc()")

    __table_args__ = (
        Index("ix_cases_status_priority", "status", "priority"),
    )


class CaseTransaction(Base):
    __tablename__ = "case_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    linking_reason = Column(String(255), nullable=True)
    linked_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    case = relationship("Case", back_populates="transactions")
    transaction = relationship("Transaction")

    __table_args__ = (
        UniqueConstraint("case_id", "transaction_id", name="uq_case_transaction"),
    )


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="SYSTEM")  # SYSTEM, REVIEWER
    actor = Column(String(128), nullable=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    metadata_json = Column(Text, nullable=True)

    case = relationship("Case", back_populates="events")

    __table_args__ = (
        Index("ix_case_events_case_timestamp", "case_id", "event_timestamp"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), index=True, nullable=False, default="ANALYST")  # ADMIN, ANALYST, VIEWER
    is_active = Column(Boolean, nullable=False, default=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False, default=utc_now)
    actor_username = Column(String(64), index=True, nullable=False, default="SYSTEM")
    actor_role = Column(String(32), nullable=True)
    record_reference = Column(String(128), index=True, nullable=True)
    status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS, FAILURE
    ip_address = Column(String(45), nullable=True)
    metadata_json = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_audit_log_timestamp_type", "timestamp", "event_type"),
        Index("ix_audit_log_actor", "actor_username", "timestamp"),
    )
