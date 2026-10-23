import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text

from app.db.models import User, AuditLog, Transaction, Case, CaseTransaction
from app.core.security import hash_password, verify_password, login_rate_limiter
from app.services import audit_service, user_service
from app.schemas.auth import UserCreate


def test_password_hashing_and_verification():
    plain = "SuperSecr3tPassword2026!"
    h = hash_password(plain)
    assert h.startswith("$2b$") or h.startswith("$2a$")
    assert verify_password(plain, h) is True
    assert verify_password("WrongPassword!", h) is False


def test_login_success_and_jwt_generation(unauthenticated_client, db_session):
    login_rate_limiter.reset()
    # Provision user
    user_service.create_user(
        db_session,
        UserCreate(
            username="investigator_sam",
            email="sam@finguard.ai",
            password="StrongAuthPassword123!",
            role="ANALYST",
        ),
    )

    # Valid login
    res = unauthenticated_client.post(
        "/api/auth/login",
        json={"username": "investigator_sam", "password": "StrongAuthPassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "investigator_sam"
    assert data["user"]["role"] == "ANALYST"


def test_login_invalid_credentials_and_rate_limiting(unauthenticated_client, db_session):
    login_rate_limiter.reset()
    user_service.create_user(
        db_session,
        UserCreate(
            username="target_user",
            email="target@finguard.ai",
            password="CorrectPassword123!",
            role="ANALYST",
        ),
    )

    # 4 bad attempts
    for _ in range(4):
        bad_res = unauthenticated_client.post(
            "/api/auth/login",
            json={"username": "target_user", "password": "WrongPassword"},
        )
        assert bad_res.status_code == 401

    # 5th bad attempt triggers rate limit lock
    fifth_res = unauthenticated_client.post(
        "/api/auth/login",
        json={"username": "target_user", "password": "WrongPassword"},
    )
    assert fifth_res.status_code in (401, 429)

    # 6th attempt is blocked by rate limiter with 429
    locked_res = unauthenticated_client.post(
        "/api/auth/login",
        json={"username": "target_user", "password": "WrongPassword"},
    )
    assert locked_res.status_code == 429
    assert "temporarily locked" in locked_res.json()["detail"]
    login_rate_limiter.reset()


def test_login_deactivated_account_rejected(unauthenticated_client, db_session):
    login_rate_limiter.reset()
    user = user_service.create_user(
        db_session,
        UserCreate(
            username="disabled_analyst",
            email="disabled@finguard.ai",
            password="ValidPassword123!",
            role="ANALYST",
        ),
    )
    user.is_active = False
    db_session.commit()

    res = unauthenticated_client.post(
        "/api/auth/login",
        json={"username": "disabled_analyst", "password": "ValidPassword123!"},
    )
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


def test_unauthenticated_requests_rejected(unauthenticated_client):
    # Protected POST cases
    res1 = unauthenticated_client.post("/api/cases", json={"title": "Unauthorized Case"})
    assert res1.status_code == 401

    # Protected GET users
    res2 = unauthenticated_client.get("/api/users")
    assert res2.status_code == 401

    # Protected GET audit
    res3 = unauthenticated_client.get("/api/audit")
    assert res3.status_code == 401


def test_viewer_role_read_only_and_write_rejection(viewer_client, db_session):
    # Viewer can read cases
    read_res = viewer_client.get("/api/cases")
    assert read_res.status_code == 200

    # Viewer CANNOT create a case
    post_res = viewer_client.post("/api/cases", json={"title": "Viewer Case Attempt"})
    assert post_res.status_code == 403
    assert "Insufficient permissions" in post_res.json()["detail"]

    # Viewer CANNOT execute assessment
    assess_res = viewer_client.post("/api/transactions/1/assess")
    assert assess_res.status_code == 403

    # Viewer CANNOT train ML model
    train_res = viewer_client.post("/api/model/train", json={"algorithm": "LOGISTIC_REGRESSION"})
    assert train_res.status_code == 403

    # Viewer CANNOT access admin users endpoint
    users_res = viewer_client.get("/api/users")
    assert users_res.status_code == 403


def test_admin_only_endpoints(client, test_analyst_user, test_admin_user, db_session):
    from app.main import app
    from app.core.deps import get_current_user

    # Analyst role -> cannot access /api/users
    app.dependency_overrides[get_current_user] = lambda: test_analyst_user
    analyst_user_res = client.get("/api/users")
    assert analyst_user_res.status_code == 403

    # Analyst role -> cannot access /api/audit
    analyst_audit_res = client.get("/api/audit")
    assert analyst_audit_res.status_code == 403

    # Admin role -> CAN access /api/users
    app.dependency_overrides[get_current_user] = lambda: test_admin_user
    admin_users_res = client.get("/api/users")
    assert admin_users_res.status_code == 200

    # Admin role -> CAN access /api/audit
    admin_audit_res = client.get("/api/audit")
    assert admin_audit_res.status_code == 200

    # Admin role -> CAN verify audit integrity
    verify_res = client.get("/api/audit/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True


def test_audit_hash_chain_integrity_and_tamper_detection(db_session):
    # 1. Record several valid audit events
    audit_service.record_audit_event(db_session, event_type="LOGIN", actor_username="alice")
    audit_service.record_audit_event(db_session, event_type="CASE_OPENED", actor_username="bob", record_reference="CASE-01")
    e3 = audit_service.record_audit_event(db_session, event_type="NOTE_ADDED", actor_username="bob", record_reference="CASE-01")

    # 2. Check initial integrity
    check1 = audit_service.verify_audit_log_integrity(db_session)
    assert check1["is_valid"] is True
    assert check1["total_records_checked"] >= 3

    # 3. Simulate unauthorized database row tampering on e3
    db_session.execute(
        text("UPDATE audit_log SET actor_username = 'malicious_impersonator' WHERE id = :id"),
        {"id": e3.id},
    )
    db_session.commit()

    # 4. Verification must detect tampering
    check2 = audit_service.verify_audit_log_integrity(db_session)
    assert check2["is_valid"] is False
    assert check2["status"] == "HASH_MISMATCH"
    assert check2["tampered_record_id"] == e3.id


def test_correlation_id_and_crlf_injection_defense(client):
    # User tries CRLF injection via X-Correlation-ID header
    injected_header = "valid-id-12345\r\nSet-Cookie: evil=session\r\nInjected: True"
    res = client.get("/health", headers={"X-Correlation-ID": injected_header})
    assert res.status_code == 200
    returned_cid = res.headers.get("X-Correlation-ID")
    assert returned_cid is not None
    # Must NOT contain newlines or carriage returns
    assert "\r" not in returned_cid
    assert "\n" not in returned_cid
    assert "Set-Cookie" not in returned_cid


def test_health_and_readiness_probes(client):
    # Liveness
    h_res = client.get("/health")
    assert h_res.status_code == 200
    assert h_res.json() == {"status": "ok"}

    # Readiness
    r_res = client.get("/api/health/ready")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["status"] == "ready"
    assert r_data["database"] == "connected"
    assert r_data["knowledge_base_rules"] > 0


def test_admin_update_user_role_and_audit_log(client, test_admin_user, test_analyst_user, db_session):
    from app.main import app
    from app.core.deps import get_current_user

    # Persist test users into the active test session
    db_session.add(test_admin_user)
    db_session.add(test_analyst_user)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: test_admin_user

    # Admin changes Analyst's role to VIEWER
    res = client.patch(
        f"/api/users/{test_analyst_user.id}/role",
        json={"role": "VIEWER"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "VIEWER"

    # Verify database was updated
    db_session.refresh(test_analyst_user)
    assert test_analyst_user.role == "VIEWER"

    # Verify USER_ROLE_UPDATED audit log entry was created
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.event_type == "USER_ROLE_UPDATED")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.actor_username == test_admin_user.username
    assert audit_entry.record_reference == test_analyst_user.username
    import json
    meta = json.loads(audit_entry.metadata_json) if isinstance(audit_entry.metadata_json, str) else audit_entry.metadata_json
    assert meta["new_role"] == "VIEWER"

    # Verify audit hash chain remains mathematically valid
    chain_check = audit_service.verify_audit_log_integrity(db_session)
    assert chain_check["is_valid"] is True


def test_admin_cannot_demote_self(client, test_admin_user, db_session):
    from app.main import app
    from app.core.deps import get_current_user

    db_session.add(test_admin_user)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: test_admin_user

    res = client.patch(
        f"/api/users/{test_admin_user.id}/role",
        json={"role": "ANALYST"},
    )
    assert res.status_code == 400
    assert "cannot demote their own active administrative account" in res.json()["detail"]


def test_unauthorized_role_change_rejection(client, test_analyst_user, test_admin_user, db_session):
    from app.main import app
    from app.core.deps import get_current_user

    db_session.add(test_admin_user)
    db_session.add(test_analyst_user)
    db_session.commit()

    # 1. Unauthenticated request -> 401
    app.dependency_overrides.pop(get_current_user, None)
    unauth_res = client.patch(
        f"/api/users/{test_analyst_user.id}/role",
        json={"role": "ADMIN"},
    )
    assert unauth_res.status_code == 401

    # 2. Analyst attempts role modification -> 403
    app.dependency_overrides[get_current_user] = lambda: test_analyst_user
    analyst_res = client.patch(
        f"/api/users/{test_admin_user.id}/role",
        json={"role": "VIEWER"},
    )
    assert analyst_res.status_code == 403

    # 3. Invalid role string -> 422
    app.dependency_overrides[get_current_user] = lambda: test_admin_user
    invalid_res = client.patch(
        f"/api/users/{test_analyst_user.id}/role",
        json={"role": "SUPERUSER"},
    )
    assert invalid_res.status_code == 422
