"""Repository helpers for users and refresh tokens.

Kept as plain functions matching the style of `repositories.py` so the service
layer never touches SQL directly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from backend.db.models import RefreshToken, User


# ---- users -----------------------------------------------------------------


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email.lower())).first()


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def create_user(
    session: Session,
    *,
    email: str,
    password_hash: str,
    role: str = "user",
) -> User:
    user = User(email=email.lower(), password_hash=password_hash, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def mark_login_success(session: Session, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    user.failed_login_count = 0
    session.add(user)
    session.commit()


def mark_login_failure(session: Session, user: User) -> None:
    user.failed_login_count = (user.failed_login_count or 0) + 1
    session.add(user)
    session.commit()


# ---- refresh tokens --------------------------------------------------------


def store_refresh_token(
    session: Session,
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
) -> RefreshToken:
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip=ip,
    )
    session.add(rt)
    session.commit()
    session.refresh(rt)
    return rt


def find_active_refresh_token(session: Session, token_hash: str) -> Optional[RefreshToken]:
    rt = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).first()
    if rt is None:
        return None
    if rt.revoked_at is not None:
        return None
    expires_at = rt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    return rt


def revoke_refresh_token(session: Session, rt: RefreshToken) -> None:
    rt.revoked_at = datetime.now(timezone.utc)
    session.add(rt)
    session.commit()


def revoke_all_user_tokens(session: Session, user_id: int) -> int:
    rows = session.exec(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)  # type: ignore[union-attr]
        )
    ).all()
    now = datetime.now(timezone.utc)
    for rt in rows:
        rt.revoked_at = now
        session.add(rt)
    session.commit()
    return len(rows)
