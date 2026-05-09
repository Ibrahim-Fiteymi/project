"""FastAPI dependencies for authenticated routes."""

from __future__ import annotations

from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from backend.auth.tokens import TokenError, decode_access_token
from backend.db import get_session
from backend.db import repositories_auth
from backend.db.models import User

# auto_error=False so we can return 401 with our own JSON shape rather than the
# default FastAPI 403 when the header is missing.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(_oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject")
    user = repositories_auth.get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not available")
    return user


def require_role(*allowed: str):
    """Dependency factory: only users whose ``role`` is in ``allowed`` may pass."""

    allowed_set = set(allowed)

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_set:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return _checker


def _client_meta(request) -> tuple[str | None, str | None]:
    ua = request.headers.get("user-agent")
    if ua:
        ua = ua[:255]
    ip = request.client.host if request.client else None
    return ua, ip


__all__ = ["get_current_user", "require_role"]


def require_any(roles: Iterable[str]):
    """Alias of :func:`require_role` accepting an iterable for ergonomics."""
    return require_role(*roles)
