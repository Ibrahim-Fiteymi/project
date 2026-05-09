"""Tests for /auth/* and access control on the analysis routes."""

from __future__ import annotations

import uuid


def _new_email() -> str:
    return f"u-{uuid.uuid4().hex[:8]}@example.com"


def test_register_returns_token_pair(anon_client):
    res = anon_client.post(
        "/auth/register",
        json={"email": _new_email(), "password": "supersecret-123"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "user"
    assert body["user"]["is_active"] is True


def test_login_with_valid_password(anon_client):
    email = _new_email()
    pwd = "another-strong-pw"
    anon_client.post("/auth/register", json={"email": email, "password": pwd})
    res = anon_client.post("/auth/login", json={"email": email, "password": pwd})
    assert res.status_code == 200, res.text
    assert res.json()["access_token"]


def test_login_wrong_password_is_401(anon_client):
    email = _new_email()
    anon_client.post("/auth/register", json={"email": email, "password": "right-pw-12345"})
    res = anon_client.post("/auth/login", json={"email": email, "password": "WRONG-pw-12345"})
    assert res.status_code == 401


def test_register_duplicate_email_is_409(anon_client):
    email = _new_email()
    anon_client.post("/auth/register", json={"email": email, "password": "x" * 12})
    res = anon_client.post("/auth/register", json={"email": email, "password": "x" * 12})
    assert res.status_code == 409


def test_refresh_rotates_token(anon_client):
    email = _new_email()
    pwd = "rotating-pw-12345"
    first = anon_client.post(
        "/auth/register", json={"email": email, "password": pwd}
    ).json()
    second = anon_client.post(
        "/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert second.status_code == 200, second.text
    assert second.json()["refresh_token"] != first["refresh_token"]
    # Original refresh token is now revoked and cannot be reused.
    third = anon_client.post(
        "/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert third.status_code == 401


def test_me_requires_auth(anon_client):
    assert anon_client.get("/auth/me").status_code == 401


def test_me_returns_caller(client):
    res = client.get("/auth/me")
    assert res.status_code == 200
    assert res.json()["role"] == "user"


def test_analysis_routes_require_auth(anon_client, upload_png):
    name, payload, ctype = upload_png
    assert anon_client.post(
        "/api/analyze", files={"file": (name, payload, ctype)}
    ).status_code == 401
    assert anon_client.get("/api/analyses").status_code == 401
    assert anon_client.get("/api/analyses/whatever").status_code == 401
    assert anon_client.delete("/api/analyses/whatever").status_code == 401


def test_users_only_see_their_own_history(anon_client, upload_png):
    name, payload, ctype = upload_png

    a = anon_client.post(
        "/auth/register", json={"email": _new_email(), "password": "user-a-pw-12"}
    ).json()
    b = anon_client.post(
        "/auth/register", json={"email": _new_email(), "password": "user-b-pw-12"}
    ).json()

    headers_a = {"Authorization": f"Bearer {a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {b['access_token']}"}

    job_a = anon_client.post(
        "/api/analyze", files={"file": (name, payload, ctype)}, headers=headers_a
    ).json()["job_id"]

    # B's history must not contain A's job.
    b_hist = anon_client.get("/api/analyses", headers=headers_b).json()
    assert all(item["job_id"] != job_a for item in b_hist["items"])
    # B cannot fetch A's job by ID either.
    assert anon_client.get(
        f"/api/analyses/{job_a}", headers=headers_b
    ).status_code == 404
