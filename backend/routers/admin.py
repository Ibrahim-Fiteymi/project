"""Admin API: user listing, role/active changes, audit log read.

Each route is gated by a single permission. Permission rules:
- USERS_READ          -> GET  /admin/users
- USERS_UPDATE        -> PATCH /admin/users/{id}/active
- USERS_UPDATE        -> PATCH /admin/users/{id}/role  (between non-elevated roles)
- ROLES_MANAGE        -> PATCH /admin/users/{id}/role  (when target/new role is admin or superadmin)
- AUDIT_LOGS_READ     -> GET  /admin/audit-logs

Every state-changing call writes an audit_logs row.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.auth.dependencies import require_permission
from backend.auth.permissions import (
    ALL_ROLES,
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
    Permission,
    has_permission,
)
from backend.db import get_session
from backend.db.models import User
from backend.services import audit_service

router = APIRouter(prefix="/admin", tags=["admin"])

_ELEVATED_ROLES = {ROLE_ADMIN, ROLE_SUPERADMIN}


class AdminUserItem(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class AdminUserList(BaseModel):
    items: list[AdminUserItem]
    total: int


class RoleChangeRequest(BaseModel):
    role: str = Field(min_length=1, max_length=32)


class ActiveChangeRequest(BaseModel):
    is_active: bool


class AuditLogItem(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    extra: dict[str, Any] = {}
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogItem]
    total: int


def _to_admin_user(u: User) -> AdminUserItem:
    return AdminUserItem(
        id=u.id or 0,
        email=u.email,
        role=u.role,
        is_active=u.is_active,
        last_login_at=u.last_login_at,
        created_at=u.created_at,
    )


@router.get("/users", response_model=AdminUserList)
def list_users(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
    _: User = Depends(require_permission(Permission.USERS_READ)),
) -> AdminUserList:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    rows = list(
        session.exec(
            select(User).order_by(User.id).offset(offset).limit(limit)
        ).all()
    )
    return AdminUserList(items=[_to_admin_user(u) for u in rows], total=len(rows))


@router.patch("/users/{user_id}/role", response_model=AdminUserItem)
def change_user_role(
    user_id: int,
    payload: RoleChangeRequest = Body(...),
    request: Request = None,  # type: ignore[assignment]
    session: Session = Depends(get_session),
    actor: User = Depends(require_permission(Permission.USERS_UPDATE)),
) -> AdminUserItem:
    new_role = payload.role.strip()
    if new_role not in ALL_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown role '{new_role}'. Allowed: {', '.join(ALL_ROLES)}.",
        )

    target = session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    # roles:manage required to grant or revoke any elevated role.
    elevation_touched = (target.role in _ELEVATED_ROLES) or (new_role in _ELEVATED_ROLES)
    if elevation_touched and not has_permission(actor.role, Permission.ROLES_MANAGE):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: roles:manage (required to touch admin/superadmin)",
        )

    # Refuse to demote the last superadmin — locks-yourself-out is a real
    # foot-gun in a course demo.
    if target.role == ROLE_SUPERADMIN and new_role != ROLE_SUPERADMIN:
        remaining = session.exec(
            select(User).where(User.role == ROLE_SUPERADMIN, User.id != target.id)
        ).first()
        if remaining is None:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last superadmin",
            )

    previous = target.role
    target.role = new_role
    session.add(target)
    session.commit()
    session.refresh(target)

    audit_service.record(
        session,
        actor_user_id=actor.id,
        action="admin.user.role_change",
        target_type="user",
        target_id=str(target.id),
        request=request,
        extra={"from": previous, "to": new_role},
    )
    return _to_admin_user(target)


@router.patch("/users/{user_id}/active", response_model=AdminUserItem)
def change_user_active(
    user_id: int,
    payload: ActiveChangeRequest = Body(...),
    request: Request = None,  # type: ignore[assignment]
    session: Session = Depends(get_session),
    actor: User = Depends(require_permission(Permission.USERS_UPDATE)),
) -> AdminUserItem:
    target = session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    if target.id == actor.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    if (
        target.role in _ELEVATED_ROLES
        and not has_permission(actor.role, Permission.ROLES_MANAGE)
    ):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: roles:manage (required to deactivate admin/superadmin)",
        )

    if (
        target.role == ROLE_SUPERADMIN
        and payload.is_active is False
    ):
        remaining = session.exec(
            select(User).where(
                User.role == ROLE_SUPERADMIN,
                User.is_active == True,  # noqa: E712
                User.id != target.id,
            )
        ).first()
        if remaining is None:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the last active superadmin",
            )

    previous = target.is_active
    target.is_active = payload.is_active
    session.add(target)
    session.commit()
    session.refresh(target)

    audit_service.record(
        session,
        actor_user_id=actor.id,
        action="admin.user.active_change",
        target_type="user",
        target_id=str(target.id),
        request=request,
        extra={"from": previous, "to": payload.is_active},
    )
    return _to_admin_user(target)


@router.get("/audit-logs", response_model=AuditLogList)
def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    _: User = Depends(require_permission(Permission.AUDIT_LOGS_READ)),
) -> AuditLogList:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    rows = audit_service.list_recent(session, limit=limit, offset=offset)
    return AuditLogList(
        items=[
            AuditLogItem(
                id=r.id or 0,
                actor_user_id=r.actor_user_id,
                action=r.action,
                target_type=r.target_type,
                target_id=r.target_id,
                ip=r.ip,
                user_agent=r.user_agent,
                extra=r.extra or {},
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=len(rows),
    )


__all__ = ["router"]
