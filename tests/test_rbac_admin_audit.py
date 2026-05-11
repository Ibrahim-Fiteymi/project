"""Phase 3 coverage: RBAC matrix, /admin/* routes, and audit log writes.

Naming is intentionally generic ("admin", "researcher") so the role names from
backend.auth.permissions stay the source of truth.
"""

from __future__ import annotations

import uuid

import pytest

from backend.auth.permissions import (
    ALL_ROLES,
    ROLE_ADMIN,
    ROLE_RESEARCHER,
    ROLE_REVIEWER,
    ROLE_SUPERADMIN,
    Permission,
    has_permission,
)


# ---------------------------------------------------------------------------
# 1. permission matrix unit tests (in-memory; no DB required)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "role,perm,expected",
    [
        (ROLE_RESEARCHER, Permission.ANALYSIS_CREATE, True),
        (ROLE_RESEARCHER, Permission.ANALYSIS_READ_OWN, True),
        (ROLE_RESEARCHER, Permission.ANALYSIS_DELETE_OWN, True),
        (ROLE_RESEARCHER, Permission.ANALYSIS_READ_ALL, False),
        (ROLE_RESEARCHER, Permission.ANALYSIS_DELETE_ALL, False),
        (ROLE_RESEARCHER, Permission.USERS_READ, False),
        (ROLE_RESEARCHER, Permission.USERS_UPDATE, False),
        (ROLE_RESEARCHER, Permission.ROLES_MANAGE, False),
        (ROLE_RESEARCHER, Permission.AUDIT_LOGS_READ, False),
        (ROLE_REVIEWER, Permission.ANALYSIS_READ_ALL, True),
        (ROLE_REVIEWER, Permission.ANALYSIS_DELETE_ALL, False),
        (ROLE_REVIEWER, Permission.USERS_READ, False),
        (ROLE_ADMIN, Permission.USERS_READ, True),
        (ROLE_ADMIN, Permission.USERS_UPDATE, True),
        (ROLE_ADMIN, Permission.AUDIT_LOGS_READ, True),
        (ROLE_ADMIN, Permission.ANALYSIS_DELETE_ALL, True),
        (ROLE_ADMIN, Permission.ROLES_MANAGE, False),
        (ROLE_SUPERADMIN, Permission.ROLES_MANAGE, True),
        (ROLE_SUPERADMIN, Permission.USERS_UPDATE, True),
        (ROLE_SUPERADMIN, Permission.AUDIT_LOGS_READ, True),
        (None, Permission.ANALYSIS_CREATE, False),
        ("nonexistent-role", Permission.ANALYSIS_CREATE, False),
    ],
)
def test_permission_matrix(role, perm, expected):
    assert has_permission(role, perm) is expected


def test_all_roles_listed():
    assert set(ALL_ROLES) == {
        ROLE_RESEARCHER, ROLE_REVIEWER, ROLE_ADMIN, ROLE_SUPERADMIN,
    }


# ---------------------------------------------------------------------------
# 2. researcher (default) cannot reach admin routes
# ---------------------------------------------------------------------------


def test_researcher_blocked_from_admin_users(client):
    res = client.get("/admin/users")
    assert res.status_code == 403
    assert "users:read" in res.json()["detail"]


def test_researcher_blocked_from_audit_logs(client):
    res = client.get("/admin/audit-logs")
    assert res.status_code == 403


def test_researcher_blocked_from_role_change(client):
    res = client.patch("/admin/users/1/role", json={"role": "admin"})
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# 3. admin can list users + flip active + read audit logs
# ---------------------------------------------------------------------------


def test_admin_can_list_users(admin_client):
    res = admin_client.get("/admin/users")
    assert res.status_code == 200, res.text
    body = res.json()
    assert isinstance(body["items"], list)
    # The admin's own row should be present.
    assert any(u["role"] == ROLE_ADMIN for u in body["items"])


def test_admin_can_read_audit_logs(admin_client):
    res = admin_client.get("/admin/audit-logs")
    assert res.status_code == 200, res.text
    actions = [r["action"] for r in res.json()["items"]]
    # admin_client registered + logged in -> at least these actions exist.
    assert "auth.register" in actions
    assert "auth.login" in actions


def test_admin_can_change_non_elevated_role(admin_client, anon_client):
    email = f"x-{uuid.uuid4().hex[:6]}@example.com"
    target = anon_client.post(
        "/auth/register", json={"email": email, "password": "x" * 12}
    ).json()
    target_id = target["user"]["id"]

    res = admin_client.patch(
        f"/admin/users/{target_id}/role", json={"role": ROLE_REVIEWER}
    )
    assert res.status_code == 200, res.text
    assert res.json()["role"] == ROLE_REVIEWER


def test_admin_cannot_promote_to_admin_without_roles_manage(admin_client, anon_client):
    email = f"y-{uuid.uuid4().hex[:6]}@example.com"
    target = anon_client.post(
        "/auth/register", json={"email": email, "password": "y" * 12}
    ).json()
    res = admin_client.patch(
        f"/admin/users/{target['user']['id']}/role", json={"role": ROLE_ADMIN}
    )
    assert res.status_code == 403
    assert "roles:manage" in res.json()["detail"]


def test_admin_can_deactivate_then_reactivate_researcher(admin_client, anon_client):
    email = f"z-{uuid.uuid4().hex[:6]}@example.com"
    target = anon_client.post(
        "/auth/register", json={"email": email, "password": "z" * 12}
    ).json()
    tid = target["user"]["id"]

    deact = admin_client.patch(f"/admin/users/{tid}/active", json={"is_active": False})
    assert deact.status_code == 200, deact.text
    assert deact.json()["is_active"] is False

    react = admin_client.patch(f"/admin/users/{tid}/active", json={"is_active": True})
    assert react.status_code == 200
    assert react.json()["is_active"] is True


def test_admin_cannot_deactivate_self(admin_client):
    me = admin_client.get("/auth/me").json()
    res = admin_client.patch(
        f"/admin/users/{me['id']}/active", json={"is_active": False}
    )
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# 4. superadmin can promote/demote into elevated roles
# ---------------------------------------------------------------------------


def test_superadmin_can_promote_to_admin(superadmin_client, anon_client):
    email = f"p-{uuid.uuid4().hex[:6]}@example.com"
    target = anon_client.post(
        "/auth/register", json={"email": email, "password": "p" * 12}
    ).json()
    res = superadmin_client.patch(
        f"/admin/users/{target['user']['id']}/role", json={"role": ROLE_ADMIN}
    )
    assert res.status_code == 200, res.text
    assert res.json()["role"] == ROLE_ADMIN


def test_unknown_role_rejected(superadmin_client, anon_client):
    email = f"q-{uuid.uuid4().hex[:6]}@example.com"
    target = anon_client.post(
        "/auth/register", json={"email": email, "password": "q" * 12}
    ).json()
    res = superadmin_client.patch(
        f"/admin/users/{target['user']['id']}/role", json={"role": "wizard"}
    )
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# 5. Reviewer can see all jobs (analysis:read_all) but not delete others'
# ---------------------------------------------------------------------------


def test_reviewer_sees_all_history_but_not_others_jobs_when_deleting(
    superadmin_client, anon_client, upload_png
):
    name, payload, ctype = upload_png

    # Create a researcher user A and have them create a job.
    a = anon_client.post(
        "/auth/register",
        json={"email": f"a-{uuid.uuid4().hex[:6]}@example.com", "password": "x" * 12},
    ).json()
    headers_a = {"Authorization": f"Bearer {a['access_token']}"}
    job_a = anon_client.post(
        "/api/analyze", files={"file": (name, payload, ctype)}, headers=headers_a
    ).json()["job_id"]

    # Create a reviewer user B.
    b_email = f"b-{uuid.uuid4().hex[:6]}@example.com"
    b_pwd = "x" * 12
    anon_client.post("/auth/register", json={"email": b_email, "password": b_pwd})
    superadmin_client.patch(
        f"/admin/users/{anon_client.post('/auth/login', json={'email': b_email, 'password': b_pwd}).json()['user']['id']}/role",
        json={"role": ROLE_REVIEWER},
    )
    b_login = anon_client.post(
        "/auth/login", json={"email": b_email, "password": b_pwd}
    ).json()
    headers_b = {"Authorization": f"Bearer {b_login['access_token']}"}

    # Reviewer sees A's job in history.
    hist = anon_client.get("/api/analyses", headers=headers_b).json()
    assert any(item["job_id"] == job_a for item in hist["items"])
    # Reviewer can fetch it by ID.
    assert anon_client.get(
        f"/api/analyses/{job_a}", headers=headers_b
    ).status_code == 200
    # But reviewer CANNOT delete A's job (no analysis:delete_all).
    assert anon_client.delete(
        f"/api/analyses/{job_a}", headers=headers_b
    ).status_code == 404


def test_admin_can_delete_others_jobs(admin_client, anon_client, upload_png):
    name, payload, ctype = upload_png
    a = anon_client.post(
        "/auth/register",
        json={"email": f"d-{uuid.uuid4().hex[:6]}@example.com", "password": "x" * 12},
    ).json()
    headers_a = {"Authorization": f"Bearer {a['access_token']}"}
    job_a = anon_client.post(
        "/api/analyze", files={"file": (name, payload, ctype)}, headers=headers_a
    ).json()["job_id"]

    res = admin_client.delete(f"/api/analyses/{job_a}")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# 6. Audit log content
# ---------------------------------------------------------------------------


def test_audit_log_records_login_failure(anon_client, admin_client):
    email = f"aud-{uuid.uuid4().hex[:6]}@example.com"
    anon_client.post("/auth/register", json={"email": email, "password": "x" * 12})
    anon_client.post("/auth/login", json={"email": email, "password": "WRONG-pw-1"})
    logs = admin_client.get("/admin/audit-logs").json()["items"]
    assert any(
        log["action"] == "auth.login.failure" and log["target_id"] == email
        for log in logs
    )


def test_audit_log_records_role_change(superadmin_client, anon_client):
    target = anon_client.post(
        "/auth/register",
        json={"email": f"r-{uuid.uuid4().hex[:6]}@example.com", "password": "x" * 12},
    ).json()
    superadmin_client.patch(
        f"/admin/users/{target['user']['id']}/role", json={"role": ROLE_REVIEWER}
    )
    logs = superadmin_client.get("/admin/audit-logs").json()["items"]
    role_changes = [log for log in logs if log["action"] == "admin.user.role_change"]
    assert role_changes, "expected at least one admin.user.role_change entry"
    latest = role_changes[0]
    assert latest["extra"]["from"] == ROLE_RESEARCHER
    assert latest["extra"]["to"] == ROLE_REVIEWER


def test_audit_log_records_analysis_deletion(client, upload_png):
    name, payload, ctype = upload_png
    job = client.post("/api/analyze", files={"file": (name, payload, ctype)}).json()
    assert client.delete(f"/api/analyses/{job['job_id']}").status_code == 200

    # The researcher-fixture user can't read audit logs, so re-validate via DB.
    from backend.db import engine
    from backend.db.models import AuditLog
    from sqlmodel import Session, select

    with Session(engine) as s:
        rows = s.exec(
            select(AuditLog).where(AuditLog.action == "analysis.delete")
        ).all()
        assert any(r.target_id == job["job_id"] for r in rows)
