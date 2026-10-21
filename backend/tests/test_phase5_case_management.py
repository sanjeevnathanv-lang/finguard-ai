import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.db.models import Transaction, Assessment, Case, CaseTransaction, CaseEvent


def create_sample_transaction(db, ref="TXN-CASE-001", amount=150000.0, channel="ONLINE", sender="SND-9901", receiver="RCV-9902"):
    t = Transaction(
        reference=ref,
        timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        amount=Decimal(str(amount)),
        currency="INR",
        sender_reference=sender,
        receiver_reference=receiver,
        transaction_type="TRANSFER",
        channel=channel,
        status="COMPLETED",
        dataset_provenance="MANUAL",
        is_synthetic=False,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def test_create_case_and_reference_generation(client, db_session):
    payload = {
        "title": "Suspicious Velocity Review",
        "summary": "Investigating rapid successive transfers from sender SND-9901.",
        "priority": "HIGH",
        "assigned_reviewer": "Analyst Alice",
        "initial_note": "Initial escalation from daily alert queue.",
    }
    response = client.post("/api/cases", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["case_reference"].startswith("CASE-")
    assert data["title"] == payload["title"]
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"
    assert data["assigned_reviewer"] == "Analyst Alice"
    assert "Analyst Alice" in data["reviewer_notes"]
    assert len(data["events"]) >= 2  # CASE_CREATED + REVIEWER_NOTE


def test_case_list_and_filters(client, db_session):
    # Create two cases with distinct priorities
    c1 = client.post("/api/cases", json={"title": "High Priority Case", "priority": "HIGH"}).json()
    c2 = client.post("/api/cases", json={"title": "Low Priority Case", "priority": "LOW"}).json()

    # Filter by priority
    res_high = client.get("/api/cases?priority=HIGH")
    assert res_high.status_code == 200
    items = res_high.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == c1["id"]

    # Search keyword
    res_search = client.get("/api/cases?search=Low")
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) == 1
    assert res_search.json()["items"][0]["id"] == c2["id"]


def test_case_status_transition_validation(client, db_session):
    case = client.post("/api/cases", json={"title": "Lifecycle Test Case", "priority": "MEDIUM"}).json()
    case_id = case["id"]

    # Transition OPEN -> IN_REVIEW (allowed)
    res_patch = client.patch(f"/api/cases/{case_id}", json={"status": "IN_REVIEW"})
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "IN_REVIEW"

    # Transition directly to CLOSED via PATCH (forbidden - must use /close)
    res_invalid_close = client.patch(f"/api/cases/{case_id}", json={"status": "CLOSED"})
    assert res_invalid_close.status_code == 400
    assert "dedicated /close endpoint" in res_invalid_close.json()["detail"]


def test_link_and_unlink_transactions(client, db_session):
    t1 = create_sample_transaction(db_session, ref="TXN-LINK-01")
    t2 = create_sample_transaction(db_session, ref="TXN-LINK-02")
    case = client.post("/api/cases", json={"title": "Linking Test Case"}).json()
    case_id = case["id"]

    # Link t1
    link_res = client.post(
        f"/api/cases/{case_id}/transactions",
        json={"transaction_id": t1.id, "linking_reason": "Primary flagged transaction"},
    )
    assert link_res.status_code == 200
    assert link_res.json()["linked_transactions_count"] == 1
    assert link_res.json()["transactions"][0]["transaction_reference"] == "TXN-LINK-01"

    # Duplicate link attempt raises 409
    dup_res = client.post(
        f"/api/cases/{case_id}/transactions",
        json={"transaction_id": t1.id, "linking_reason": "Duplicate link attempt"},
    )
    assert dup_res.status_code == 409

    # Unlink t1
    unlink_res = client.delete(f"/api/cases/{case_id}/transactions/{t1.id}")
    assert unlink_res.status_code == 200
    assert unlink_res.json()["linked_transactions_count"] == 0


def test_add_reviewer_notes(client, db_session):
    case = client.post("/api/cases", json={"title": "Notes Test Case"}).json()
    case_id = case["id"]

    note_res = client.post(
        f"/api/cases/{case_id}/notes",
        json={"note": "Customer contacted to confirm beneficiary account details.", "author": "Investigator Bob"},
    )
    assert note_res.status_code == 200
    assert note_res.json()["event_type"] == "REVIEWER_NOTE"
    assert note_res.json()["actor"] == "Investigator Bob"

    # Verify notes in case details
    detail_res = client.get(f"/api/cases/{case_id}")
    assert detail_res.status_code == 200
    assert "Customer contacted to confirm" in detail_res.json()["reviewer_notes"]


def test_close_case_with_disposition(client, db_session):
    case = client.post("/api/cases", json={"title": "Close Disposition Case"}).json()
    case_id = case["id"]

    # Close with valid disposition
    close_payload = {
        "final_disposition": "CONFIRMED_LEGITIMATE",
        "disposition_notes": "Reviewed KYC paperwork and verified valid corporate supplier payment.",
        "reviewer_name": "Lead Analyst Carol",
    }
    close_res = client.post(f"/api/cases/{case_id}/close", json=close_payload)
    assert close_res.status_code == 200
    closed_data = close_res.json()

    assert closed_data["status"] == "CLOSED"
    assert closed_data["final_disposition"] == "CONFIRMED_LEGITIMATE"
    assert closed_data["closed_at"] is not None
    assert closed_data["disposition_notes"] == close_payload["disposition_notes"]

    # Attempting to close again returns 400
    second_close = client.post(f"/api/cases/{case_id}/close", json=close_payload)
    assert second_close.status_code == 400


def test_multi_source_timeline_ordering(client, db_session):
    t = create_sample_transaction(db_session, ref="TXN-TIME-001")
    # Add an assessment for t
    asmt = Assessment(
        transaction_id=t.id,
        transaction_reference=t.reference,
        final_recommendation="REVIEW",
        overall_severity="MEDIUM",
        risk_score=Decimal("55.00"),
        rules_triggered_count=2,
        engine_version="1.0.0",
        knowledge_base_version="1.0.0",
        trace_json="{}",
        model_version="1.0.0-rules-only",
    )
    db_session.add(asmt)
    db_session.commit()

    # Create case and link transaction
    case = client.post(
        "/api/cases",
        json={"title": "Timeline Case", "initial_transaction_ids": [t.id]},
    ).json()

    # Add a reviewer note
    client.post(f"/api/cases/{case['id']}/notes", json={"note": "Reviewed initial AI flags."})

    # Fetch timeline
    timeline_res = client.get(f"/api/cases/{case['id']}/timeline")
    assert timeline_res.status_code == 200
    events = timeline_res.json()

    event_types = [e["event_type"] for e in events]
    assert "TRANSACTION_OCCURRED" in event_types
    assert "ASSESSMENT_PERFORMED" in event_types
    assert "TRANSACTION_LINKED" in event_types
    assert "REVIEWER_NOTE" in event_types

    # Ensure chronologically sorted
    timestamps = [e["event_timestamp"] for e in events]
    assert timestamps == sorted(timestamps)


def test_related_transaction_analysis_factual_reasons(client, db_session):
    t1 = create_sample_transaction(db_session, ref="TXN-REL-01", sender="SND-SHARED-9", receiver="RCV-01")
    t2 = create_sample_transaction(db_session, ref="TXN-REL-02", sender="SND-SHARED-9", receiver="RCV-02")
    t3 = create_sample_transaction(db_session, ref="TXN-REL-03", sender="SND-UNRELATED", receiver="RCV-03")

    # Create case with t1 linked
    case = client.post("/api/cases", json={"title": "Relational Case", "initial_transaction_ids": [t1.id]}).json()

    res = client.get(f"/api/cases/{case['id']}/related-transactions")
    assert res.status_code == 200
    related = res.json()

    # t2 should be identified because of shared sender SND-SHARED-9
    t2_matches = [r for r in related if r["transaction_reference"] == "TXN-REL-02"]
    assert len(t2_matches) == 1
    t2_data = t2_matches[0]
    assert any("Shares sender reference 'SND-SHARED-9'" in r for r in t2_data["relationship_reasons"])
    assert t2_data["match_strength"] in ("HIGH", "MEDIUM")
    assert not t2_data["is_already_linked"]


def test_export_case_summary_formula_injection_defense(client, db_session):
    # Potential CSV/formula injection payload
    suspicious_title = "=SUM(1+1)*cmd"
    suspicious_note = "+EXCEL|'cmd.exe' /c calc"

    case = client.post("/api/cases", json={"title": suspicious_title, "initial_note": suspicious_note}).json()
    case_id = case["id"]

    export_res = client.get(f"/api/cases/{case_id}/export")
    assert export_res.status_code == 200
    export_data = export_res.json()

    assert export_data["case_reference"].startswith("CASE-")
    # Check that dangerous leading characters are escaped with a leading single quote
    assert export_data["title"].startswith("'=")
    assert "'+" in export_data["report_markdown"]
    assert "FinGuard AI Investigation Report" in export_data["report_markdown"]
