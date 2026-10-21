from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session

from app.db.models import Case, Transaction, CaseTransaction
from app.schemas.case import RelatedTransactionRead


def find_related_transactions(db: Session, case_id: int, max_results: int = 50) -> List[RelatedTransactionRead]:
    """
    Perform explainable relational analysis against persisted database transactions.
    Identifies shared counterparties, temporal proximity, and channel clustering
    relative to transactions already linked to the specified case.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return []

    linked_links = db.query(CaseTransaction).filter(CaseTransaction.case_id == case_id).all()
    if not linked_links:
        return []

    linked_txn_ids: Set[int] = {l.transaction_id for l in linked_links}
    linked_txns: List[Transaction] = (
        db.query(Transaction).filter(Transaction.id.in_(linked_txn_ids)).all()
    )

    if not linked_txns:
        return []

    # Collect search attributes from linked transactions
    senders: Dict[str, List[Transaction]] = {}
    receivers: Dict[str, List[Transaction]] = {}
    timestamps: List[datetime] = []

    for lt in linked_txns:
        if lt.sender_reference:
            senders.setdefault(lt.sender_reference.strip(), []).append(lt)
        if lt.receiver_reference:
            receivers.setdefault(lt.receiver_reference.strip(), []).append(lt)
        if lt.timestamp:
            timestamps.append(lt.timestamp)

    # Query candidate transactions from DB (excluding deleted/unreadable, but including all active)
    candidates = db.query(Transaction).all()

    related_map: Dict[int, Dict[str, Any]] = {}

    for cand in candidates:
        reasons: List[str] = []
        score = 0

        # Check shared sender
        if cand.sender_reference and cand.sender_reference.strip() in senders:
            matched_txns = senders[cand.sender_reference.strip()]
            matched_refs = ", ".join(t.reference for t in matched_txns if t.id != cand.id)
            if matched_refs:
                reasons.append(
                    f"Shares sender reference '{cand.sender_reference}' with linked transaction(s) ({matched_refs})"
                )
                score += 3

        # Check shared receiver
        if cand.receiver_reference and cand.receiver_reference.strip() in receivers:
            matched_txns = receivers[cand.receiver_reference.strip()]
            matched_refs = ", ".join(t.reference for t in matched_txns if t.id != cand.id)
            if matched_refs:
                reasons.append(
                    f"Shares receiver reference '{cand.receiver_reference}' with linked transaction(s) ({matched_refs})"
                )
                score += 3

        # Check temporal proximity (within 24 hours of any linked transaction)
        if cand.timestamp and timestamps:
            closest_diff_seconds = None
            closest_ref = None
            for lt in linked_txns:
                if lt.id == cand.id or not lt.timestamp:
                    continue
                # Ensure UTC
                t1 = cand.timestamp if cand.timestamp.tzinfo else cand.timestamp.replace(tzinfo=timezone.utc)
                t2 = lt.timestamp if lt.timestamp.tzinfo else lt.timestamp.replace(tzinfo=timezone.utc)
                diff = abs((t1 - t2).total_seconds())
                if diff <= 86400:  # 24 hours
                    if closest_diff_seconds is None or diff < closest_diff_seconds:
                        closest_diff_seconds = diff
                        closest_ref = lt.reference

            if closest_diff_seconds is not None and closest_ref is not None:
                hours = closest_diff_seconds / 3600.0
                reasons.append(
                    f"Occurred within {hours:.1f}h window of linked transaction '{closest_ref}'"
                )
                score += 1

                # If same channel as well, add signal
                for lt in linked_txns:
                    if lt.channel == cand.channel and lt.currency == cand.currency and lt.id != cand.id:
                        reasons.append(
                            f"Shares channel '{cand.channel}' and currency '{cand.currency}' with linked '{lt.reference}'"
                        )
                        score += 1
                        break

        # Only retain if reasons exist
        if reasons:
            # Determine match strength
            if score >= 4:
                match_strength = "HIGH"
            elif score >= 2:
                match_strength = "MEDIUM"
            else:
                match_strength = "INFORMATIONAL"

            is_already = cand.id in linked_txn_ids

            related_map[cand.id] = {
                "transaction_id": cand.id,
                "transaction_reference": cand.reference,
                "timestamp": cand.timestamp,
                "amount": cand.amount,
                "currency": cand.currency,
                "transaction_type": cand.transaction_type,
                "channel": cand.channel,
                "status": cand.status,
                "sender_reference": cand.sender_reference,
                "receiver_reference": cand.receiver_reference,
                "relationship_reasons": reasons,
                "match_strength": match_strength,
                "is_already_linked": is_already,
                "score": score,
            }

    # Sort candidates: unlinked first, then by score descending, then by timestamp descending
    sorted_candidates = sorted(
        related_map.values(),
        key=lambda x: (not x["is_already_linked"], x["score"], x["timestamp"]),
        reverse=True,
    )

    result: List[RelatedTransactionRead] = []
    for item in sorted_candidates[:max_results]:
        result.append(
            RelatedTransactionRead(
                transaction_id=item["transaction_id"],
                transaction_reference=item["transaction_reference"],
                timestamp=item["timestamp"],
                amount=item["amount"],
                currency=item["currency"],
                transaction_type=item["transaction_type"],
                channel=item["channel"],
                status=item["status"],
                sender_reference=item["sender_reference"],
                receiver_reference=item["receiver_reference"],
                relationship_reasons=item["relationship_reasons"],
                match_strength=item["match_strength"],
                is_already_linked=item["is_already_linked"],
            )
        )

    return result
