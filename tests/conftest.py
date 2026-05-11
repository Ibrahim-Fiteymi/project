"""Pytest fixtures for backend integration tests.

Each test runs against a fresh SQLite database in a temp directory so the dev
DB at ``backend/storage/deeply.db`` is never touched.

The default ``client`` fixture registers a user and attaches a Bearer token to
every request so that pre-auth tests keep passing unchanged. ``anon_client``
returns an unauthenticated client for asserting 401 behaviour explicitly.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import uuid
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# These overrides MUST happen before any `backend.*` module is imported, because
# `backend.config.Settings()` is instantiated at import time and locks in
# `storage_root`. Some test modules (e.g. test_rate_limit.py) import `backend`
# at module top level, so a fixture would run too late.
_TEST_STORAGE = Path(tempfile.mkdtemp(prefix="nuclei-tests-"))
os.environ.setdefault("STORAGE_ROOT", str(_TEST_STORAGE))
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("RATE_LIMIT_UPLOAD_PER_MINUTE", "100")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production")


@pytest.fixture(scope="session", autouse=True)
def _isolated_storage():
    """Sanity check: confirm the env overrides above are still in force."""
    assert os.environ["STORAGE_ROOT"] == str(_TEST_STORAGE)
    yield _TEST_STORAGE


def _boot_app():
    """Late import so the env overrides above apply."""
    from fastapi.testclient import TestClient

    from backend.db import init_db
    from backend.main import app, upload_limiter

    upload_limiter.reset()
    init_db()
    return TestClient(app)


@pytest.fixture()
def anon_client(_isolated_storage):
    """A TestClient without any Authorization header — for 401 assertions."""
    with _boot_app() as c:
        yield c


@pytest.fixture()
def client(_isolated_storage):
    """A TestClient pre-authenticated as a fresh per-test user."""
    with _boot_app() as c:
        email = f"user-{uuid.uuid4().hex[:8]}@example.com"
        password = "test-pass-1234"
        res = c.post("/auth/register", json={"email": email, "password": password})
        assert res.status_code == 201, res.text
        token = res.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c


def _promote_and_login(c, email: str, password: str, role: str) -> None:
    from backend.db import get_session
    from backend.db import repositories_auth

    gen = get_session()
    session = next(gen)
    try:
        user = repositories_auth.get_user_by_email(session, email)
        assert user is not None
        user.role = role
        session.add(user)
        session.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
    re = c.post("/auth/login", json={"email": email, "password": password})
    assert re.status_code == 200, re.text
    c.headers.update({"Authorization": f"Bearer {re.json()['access_token']}"})


@pytest.fixture()
def admin_client(_isolated_storage):
    """A TestClient authenticated as an `admin`-role user."""
    with _boot_app() as c:
        email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
        password = "admin-pw-1234"
        res = c.post("/auth/register", json={"email": email, "password": password})
        assert res.status_code == 201, res.text
        _promote_and_login(c, email, password, "admin")
        yield c


@pytest.fixture()
def superadmin_client(_isolated_storage):
    """A TestClient authenticated as a `superadmin` (roles:manage)."""
    with _boot_app() as c:
        email = f"super-{uuid.uuid4().hex[:8]}@example.com"
        password = "super-pw-12345"
        res = c.post("/auth/register", json={"email": email, "password": password})
        assert res.status_code == 201, res.text
        _promote_and_login(c, email, password, "superadmin")
        yield c


@pytest.fixture()
def sample_png_bytes() -> bytes:
    """A small synthetic PNG with bright blobs to exercise the fallback path."""
    rng = np.random.default_rng(42)
    img = (rng.random((128, 128, 3)) * 80).astype(np.uint8)
    # Stamp a few bright circles so even the Otsu fallback finds components.
    for cx, cy in [(30, 30), (95, 40), (60, 90), (100, 100)]:
        yy, xx = np.ogrid[:128, :128]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= 36
        img[mask] = 240
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def upload_png(sample_png_bytes: bytes):
    """Return a (filename, bytes, content_type) tuple ready for FastAPI's TestClient."""
    return ("sample.png", sample_png_bytes, "image/png")
