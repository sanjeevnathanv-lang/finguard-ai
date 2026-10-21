from datetime import timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import Transaction
from app.ai.facts import Fact, FactSet, FactSource

def extract_facts_from_transaction(transaction: Transaction, db: Optional[Session] = None) -> FactSet:
    """
    Extract typed, source-attributed domain facts from a transaction record,
    supplemented by historical velocity queries over the database.
    """
    facts = FactSet()

    # 1. Base transaction attributes
    facts.add_fact(Fact(
        name="amount",
        value=Decimal(str(transaction.amount)),
        data_type="NUMBER",
        source=FactSource.TRANSACTION_ATTRIBUTE,
        description="Transaction monetary magnitude",
    ))
    facts.add_fact(Fact(
        name="currency",
        value=transaction.currency.upper(),
        data_type="STRING",
        source=FactSource.TRANSACTION_ATTRIBUTE,
        description="ISO 4217 currency code",
    ))
    facts.add_fact(Fact(
        name="transaction_type",
        value=transaction.transaction_type.upper(),
        data_type="STRING",
        source=FactSource.TRANSACTION_ATTRIBUTE,
        description="Operational classification of transfer",
    ))
    facts.add_fact(Fact(
        name="channel",
        value=transaction.channel.upper(),
        data_type="STRING",
        source=FactSource.TRANSACTION_ATTRIBUTE,
        description="Delivery and origination medium",
    ))
    facts.add_fact(Fact(
        name="status",
        value=transaction.status.upper(),
        data_type="STRING",
        source=FactSource.TRANSACTION_ATTRIBUTE,
        description="Transaction lifecycle status",
    ))

    # Sender / Receiver references (handle missing information explicitly)
    if transaction.sender_reference:
        facts.add_fact(Fact(
            name="sender_reference",
            value=transaction.sender_reference,
            data_type="STRING",
            source=FactSource.TRANSACTION_ATTRIBUTE,
            description="Pseudonymized originator identifier",
        ))
    else:
        facts.add_fact(Fact(
            name="sender_reference",
            value=None,
            data_type="UNKNOWN",
            source=FactSource.DATA_QUALITY,
            description="Originator identifier absent from transaction payload",
        ))

    if transaction.receiver_reference:
        facts.add_fact(Fact(
            name="receiver_reference",
            value=transaction.receiver_reference,
            data_type="STRING",
            source=FactSource.TRANSACTION_ATTRIBUTE,
            description="Pseudonymized beneficiary/merchant identifier",
        ))
    else:
        facts.add_fact(Fact(
            name="receiver_reference",
            value=None,
            data_type="UNKNOWN",
            source=FactSource.DATA_QUALITY,
            description="Beneficiary identifier absent from transaction payload",
        ))

    # 2. Temporal context
    ts = transaction.timestamp
    facts.add_fact(Fact(
        name="hour_of_day",
        value=ts.hour,
        data_type="NUMBER",
        source=FactSource.TEMPORAL_CONTEXT,
        description="Hour of occurrence in UTC (0-23)",
    ))
    facts.add_fact(Fact(
        name="day_of_week",
        value=ts.weekday(),
        data_type="NUMBER",
        source=FactSource.TEMPORAL_CONTEXT,
        description="Day of week (0=Monday, 6=Sunday)",
    ))
    facts.add_fact(Fact(
        name="is_weekend",
        value=ts.weekday() in (5, 6),
        data_type="BOOLEAN",
        source=FactSource.TEMPORAL_CONTEXT,
        description="Occurred on Saturday or Sunday",
    ))

    # 3. Historical Velocity Queries (if database session and sender provided)
    if db is not None and transaction.sender_reference:
        one_hour_prior = ts - timedelta(hours=1)
        # Query count of previous transactions from this sender in 1h window
        velocity_1h = (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.sender_reference == transaction.sender_reference,
                Transaction.timestamp >= one_hour_prior,
                Transaction.timestamp <= ts,
                Transaction.id != (transaction.id or 0),
            )
            .scalar()
            or 0
        )
        facts.add_fact(Fact(
            name="sender_txn_count_1h",
            value=velocity_1h + 1,  # Include current transaction
            data_type="NUMBER",
            source=FactSource.HISTORICAL_VELOCITY,
            description=f"Transaction occurrences for sender '{transaction.sender_reference}' within 60-minute window",
        ))
    else:
        # Default velocity to 1 if standalone or no history available
        facts.add_fact(Fact(
            name="sender_txn_count_1h",
            value=1,
            data_type="NUMBER",
            source=FactSource.HISTORICAL_VELOCITY,
            description="Default baseline single transaction velocity",
        ))

    return facts
