"""Database Schema Migration Subsystem for FinGuard AI.
Provides safe, idempotent, versioned DDL migrations for SQLite/SQLAlchemy.
"""

from datetime import datetime, timezone
import logging
from typing import List, Tuple
from sqlalchemy import text, Engine
from app.db.session import engine as default_engine

logger = logging.getLogger("finguard.migrations")


def init_migrations_table(conn) -> None:
    """Ensure the schema_migrations tracking table exists."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name VARCHAR(64) UNIQUE NOT NULL,
            applied_at DATETIME NOT NULL,
            description TEXT
        )
    """))


def get_applied_migrations(conn) -> List[str]:
    """Retrieve list of already applied migration identifiers."""
    init_migrations_table(conn)
    result = conn.execute(text("SELECT migration_name FROM schema_migrations ORDER BY id ASC"))
    return [row[0] for row in result.fetchall()]


def record_migration(conn, migration_name: str, description: str = "") -> None:
    """Record a migration as applied."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        text("INSERT INTO schema_migrations (migration_name, applied_at, description) VALUES (:name, :ts, :desc)"),
        {"name": migration_name, "ts": now, "desc": description}
    )


def get_table_columns(conn, table_name: str) -> List[str]:
    """Retrieve existing column names for a given SQLite table."""
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    return [row[1] for row in result.fetchall()]


def migration_001_phase4_hybrid_assessment_columns(conn) -> None:
    """
    Phase 4 Migration:
    Add 'model_version' and 'hybrid_report_json' columns to 'assessments' table if not present.
    Both columns are nullable to guarantee complete compatibility with existing records.
    """
    columns = get_table_columns(conn, "assessments")

    if "model_version" not in columns:
        logger.info("Adding column 'model_version' to 'assessments' table...")
        conn.execute(text("ALTER TABLE assessments ADD COLUMN model_version VARCHAR(32) NULL"))

    if "hybrid_report_json" not in columns:
        logger.info("Adding column 'hybrid_report_json' to 'assessments' table...")
        conn.execute(text("ALTER TABLE assessments ADD COLUMN hybrid_report_json TEXT NULL"))


def migration_002_phase5_case_management_and_timeline(conn) -> None:
    """
    Phase 5 Migration:
    Create 'cases', 'case_transactions', and 'case_events' tables with constraints and indexes.
    Preserves all existing data in transactions and assessments tables.
    """
    logger.info("Executing Phase 5 investigation case management migration...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_reference VARCHAR(64) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            summary TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
            priority VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
            assigned_reviewer VARCHAR(128),
            reviewer_notes TEXT,
            final_disposition VARCHAR(64),
            disposition_notes TEXT,
            closed_at DATETIME,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cases_case_reference ON cases (case_reference)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cases_status_priority ON cases (status, priority)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS case_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            transaction_id INTEGER NOT NULL,
            linking_reason VARCHAR(255),
            linked_at DATETIME NOT NULL,
            FOREIGN KEY(case_id) REFERENCES cases (id) ON DELETE CASCADE,
            FOREIGN KEY(transaction_id) REFERENCES transactions (id) ON DELETE CASCADE,
            CONSTRAINT uq_case_transaction UNIQUE (case_id, transaction_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_case_transactions_case_id ON case_transactions (case_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_case_transactions_transaction_id ON case_transactions (transaction_id)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS case_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            source VARCHAR(32) NOT NULL DEFAULT 'SYSTEM',
            actor VARCHAR(128),
            event_timestamp DATETIME NOT NULL,
            metadata_json TEXT,
            FOREIGN KEY(case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_case_events_case_timestamp ON case_events (case_id, event_timestamp)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_case_events_case_id ON case_events (case_id)"))


def migration_003_phase6_security_users_and_audit_log(conn) -> None:
    """
    Phase 6 Migration:
    Create 'users' and 'audit_log' tables with role-based access control, account state,
    and cryptographic hash chain audit infrastructure.
    Preserves all existing data in transactions, assessments, and cases tables.
    """
    logger.info("Executing Phase 6 security, user auth, and audit log migration...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(128) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(128),
            role VARCHAR(32) NOT NULL DEFAULT 'ANALYST',
            is_active BOOLEAN NOT NULL DEFAULT 1,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until DATETIME,
            last_login_at DATETIME,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_role_active ON users (role, is_active)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type VARCHAR(64) NOT NULL,
            timestamp DATETIME NOT NULL,
            actor_username VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
            actor_role VARCHAR(32),
            record_reference VARCHAR(128),
            status VARCHAR(32) NOT NULL DEFAULT 'SUCCESS',
            ip_address VARCHAR(45),
            metadata_json TEXT,
            previous_hash VARCHAR(64),
            event_hash VARCHAR(64) NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_log_timestamp_type ON audit_log (timestamp, event_type)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_log_actor ON audit_log (actor_username, timestamp)"))


# Registry of ordered migrations
MIGRATIONS: List[Tuple[str, str, callable]] = [
    (
        "001_phase4_hybrid_assessment_columns",
        "Add model_version and hybrid_report_json to assessments table",
        migration_001_phase4_hybrid_assessment_columns,
    ),
    (
        "002_phase5_case_management_and_timeline",
        "Create cases, case_transactions, and case_events tables for investigation workflow",
        migration_002_phase5_case_management_and_timeline,
    ),
    (
        "003_phase6_security_users_and_audit_log",
        "Create users and audit_log tables for role-based access control and tamper-evident audit trail",
        migration_003_phase6_security_users_and_audit_log,
    ),
]


def run_migrations(engine: Engine = default_engine) -> List[str]:
    """
    Execute all pending migrations safely and idempotently.
    Returns list of newly applied migration names.
    """
    applied_now: List[str] = []

    with engine.begin() as conn:
        already_applied = set(get_applied_migrations(conn))

        for name, description, migration_fn in MIGRATIONS:
            if name not in already_applied:
                logger.info(f"Applying migration: {name} — {description}")
                migration_fn(conn)
                record_migration(conn, name, description)
                applied_now.append(name)
            else:
                logger.debug(f"Migration {name} is already applied.")

    return applied_now


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    print("Executing FinGuard AI schema migrations...")
    applied = run_migrations()
    if applied:
        print(f"Successfully applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("Schema is already fully up to date. No pending migrations.")
