"""Analytics service for transaction pattern intelligence.
Computes empirical distributions strictly across persisted records with currency segregation.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.ml.schemas import TransactionPatternAnalytics


def compute_transaction_patterns(
    db: Session,
    currency_filter: Optional[str] = None,
) -> TransactionPatternAnalytics:
    """Compute pattern intelligence over actual persisted database records."""
    query = db.query(Transaction)
    if currency_filter:
        query = query.filter(Transaction.currency == currency_filter.upper())

    total = query.count()
    now = datetime.now(timezone.utc)

    # 1. Currency distribution
    curr_counts = (
        db.query(Transaction.currency, func.count(Transaction.id))
        .group_by(Transaction.currency)
        .all()
    )
    currency_distribution = {curr: count for curr, count in curr_counts}

    # 2. Channel distribution
    ch_query = db.query(Transaction.channel, func.count(Transaction.id))
    if currency_filter:
        ch_query = ch_query.filter(Transaction.currency == currency_filter.upper())
    channel_counts = ch_query.group_by(Transaction.channel).all()
    channel_distribution = {ch: count for ch, count in channel_counts}

    # 3. Transaction type distribution
    tt_query = db.query(Transaction.transaction_type, func.count(Transaction.id))
    if currency_filter:
        tt_query = tt_query.filter(Transaction.currency == currency_filter.upper())
    type_counts = tt_query.group_by(Transaction.transaction_type).all()
    transaction_type_distribution = {tt: count for tt, count in type_counts}

    # 4. Hourly distribution (0-23)
    hourly_distribution: Dict[int, int] = {h: 0 for h in range(24)}
    day_of_week_distribution: Dict[int, int] = {d: 0 for d in range(7)}

    # Fetch timestamps to compute localized calendar/hour distributions safely in Python
    ts_query = db.query(Transaction.timestamp)
    if currency_filter:
        ts_query = ts_query.filter(Transaction.currency == currency_filter.upper())
    timestamps = ts_query.all()

    for (ts,) in timestamps:
        if ts is not None:
            hourly_distribution[ts.hour] = hourly_distribution.get(ts.hour, 0) + 1
            hourly_distribution[ts.hour] = hourly_distribution[ts.hour]
            weekday = ts.weekday()
            day_of_week_distribution[weekday] = day_of_week_distribution.get(weekday, 0) + 1

    # 5. Top active senders
    snd_query = (
        db.query(
            Transaction.sender_reference,
            Transaction.currency,
            func.count(Transaction.id).label("txn_count"),
            func.sum(Transaction.amount).label("total_volume"),
        )
        .filter(Transaction.sender_reference.isnot(None))
    )
    if currency_filter:
        snd_query = snd_query.filter(Transaction.currency == currency_filter.upper())

    top_senders_rows = (
        snd_query.group_by(Transaction.sender_reference, Transaction.currency)
        .order_by(func.count(Transaction.id).desc())
        .limit(10)
        .all()
    )

    top_active_senders = [
        {
            "sender_reference": row[0],
            "currency": row[1],
            "transaction_count": int(row[2]),
            "total_volume": float(row[3] or 0.0),
        }
        for row in top_senders_rows
    ]

    # 6. Average and Max amounts grouped strictly by currency
    avg_by_curr = (
        db.query(Transaction.currency, func.avg(Transaction.amount))
        .group_by(Transaction.currency)
        .all()
    )
    average_amounts_by_currency = {
        curr: float(round(avg or 0.0, 2)) for curr, avg in avg_by_curr
    }

    max_by_curr = (
        db.query(Transaction.currency, func.max(Transaction.amount))
        .group_by(Transaction.currency)
        .all()
    )
    max_amounts_by_currency = {
        curr: float(round(m or 0.0, 2)) for curr, m in max_by_curr
    }

    return TransactionPatternAnalytics(
        total_analyzed_transactions=total,
        query_timestamp=now,
        currency_distribution=currency_distribution,
        channel_distribution=channel_distribution,
        transaction_type_distribution=transaction_type_distribution,
        hourly_distribution=hourly_distribution,
        day_of_week_distribution=day_of_week_distribution,
        top_active_senders=top_active_senders,
        average_amounts_by_currency=average_amounts_by_currency,
        max_amounts_by_currency=max_amounts_by_currency,
    )
