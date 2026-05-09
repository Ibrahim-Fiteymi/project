"""JWT access/refresh token helpers.

Access tokens are short-lived JWTs sent on every request.
Refresh tokens are opaque random strings; we store only their SHA-256 hash in
the DB so that a stolen DB row cannot be replayed against the API and so that
logout/rotate is a real revocation rather than a trust-the-clock bet.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from backend.config import settings

_DEV_FALLBACK_SECRET = "dev-only-not-for-production-" + secrets.token_urlsafe(16)


def _secret() -> str:
    """Return the active signing secret.

    In production a real `JWT_SECRET` must be configured; if it is missing or
    still set to the literal placeholder we refuse to start signing tokens.
    Dev mode falls back to a per-process random secret so reload doesn't
    immediately invalidate every session.
    """
    configured = settings.jwt_secret
    if configured and configured != "change-me-in-production":
        return configured
    if settings.env != "dev":
        raise RuntimeError(
            "JWT_SECRET is not set (or still the placeholder). Refusing to "
            "issue tokens outside dev mode."
        )
    return _DEV_FALLBACK_SECRET


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    *, subject: str, role: str, extra: Optional[dict[str, Any]] = None
) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(seconds=settings.jwt_access_ttl_seconds)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _secret(), algorithm=settings.jwt_alg)


@dataclass
class RefreshTokenPair:
    raw: str          # what we hand to the client
    hashed: str       # what we store
    expires_at: datetime


def create_refresh_token() -> RefreshTokenPair:
    raw = secrets.token_urlsafe(48)
    hashed = hash_refresh_token(raw)
    expires_at = _now() + timedelta(seconds=settings.jwt_refresh_ttl_seconds)
    return RefreshTokenPair(raw=raw, hashed=hashed, expires_at=expires_at)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TokenError(Exception):
    """Raised when a token is malformed, expired, or otherwise unusable."""


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[settings.jwt_alg])
    except jwt.ExpiredSignatureError as e:
        raise TokenError("Token expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenError("Invalid token") from e
    if payload.get("type") != "access":
        raise TokenError("Wrong token type")
    return payload
