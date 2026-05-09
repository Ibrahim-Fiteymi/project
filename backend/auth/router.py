"""Auth API routes: register, login, refresh, logout, me.

Token model:
- Access token (JWT, ~15 min) sent in `Authorization: Bearer ...` headers.
- Refresh token (opaque, ~30 days) stored hashed in `refresh_tokens`. The
  client keeps the raw value and sends it back to /auth/refresh; we look it
  up by SHA-256 hash, rotate it (revoke old, issue new), and return a new
  access+refresh pair.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from backend.auth.dependencies import _client_meta, get_current_user
from backend.auth.passwords import hash_password, verify_password
from backend.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.auth.tokens import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from backend.config import settings
from backend.db import get_session, repositories_auth
from backend.db.models import User

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id or 0,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


def _issue_token_pair(
    session: Session, user: User, request: Request
) -> TokenResponse:
    if user.id is None:
        raise HTTPException(status_code=500, detail="User missing id")
    access = create_access_token(subject=str(user.id), role=user.role)
    refresh = create_refresh_token()
    ua, ip = _client_meta(request)
    repositories_auth.store_refresh_token(
        session,
        user_id=user.id,
        token_hash=refresh.hashed,
        expires_at=refresh.expires_at,
        user_agent=ua,
        ip=ip,
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh.raw,
        expires_in=settings.jwt_access_ttl_seconds,
        user=_to_user_response(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> TokenResponse:
    if repositories_auth.get_user_by_email(session, payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = repositories_auth.create_user(
        session,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
    )
    repositories_auth.mark_login_success(session, user)
    return _issue_token_pair(session, user, request)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> TokenResponse:
    user = repositories_auth.get_user_by_email(session, payload.email)
    # Constant-ish error to avoid email-enumeration via timing/wording.
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        if user is not None:
            repositories_auth.mark_login_failure(session, user)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    repositories_auth.mark_login_success(session, user)
    return _issue_token_pair(session, user, request)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> TokenResponse:
    token_hash = hash_refresh_token(payload.refresh_token)
    rt = repositories_auth.find_active_refresh_token(session, token_hash)
    if rt is None:
        raise HTTPException(status_code=401, detail="Refresh token invalid or expired")
    user = repositories_auth.get_user_by_id(session, rt.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not available")
    # Rotate: revoke the presented token before issuing a new pair.
    repositories_auth.revoke_refresh_token(session, rt)
    return _issue_token_pair(session, user, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    if payload.refresh_token:
        rt = repositories_auth.find_active_refresh_token(
            session, hash_refresh_token(payload.refresh_token)
        )
        # Only revoke if the token actually belongs to the caller.
        if rt is not None and rt.user_id == user.id:
            repositories_auth.revoke_refresh_token(session, rt)
    else:
        # Best-effort full sign-out: revoke all the caller's refresh tokens.
        if user.id is not None:
            repositories_auth.revoke_all_user_tokens(session, user.id)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(user)
