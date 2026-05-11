"""Audit logging service.

A thin wrapper over the AuditLog model so callers can use a single function
signature regardless of context (web request, background job, CLI). Failures
to write the audit log are logged but never raised — losing an audit row is
preferable to failing the user-visible operation it describes.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import Request
from sqlmodel import Session, select

from backend.db.models import AuditLog

log = logging.getLogger(__name__)


def _client_meta(request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
    if request is None:
        return None, None
    ua = request.headers.get("user-agent")
    if ua:
        ua = ua[:255]
    ip = request.client.host if request.client else None
    return ua, ip


def record(
    session: Session,
    *,
    actor_user_id: Optional[int],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    request: Optional[Request] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    ua, ip = _client_meta(request)
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action[:64],
        target_type=target_type[:32] if target_type else None,
        target_id=target_id[:64] if target_id else None,
        ip=ip,
        user_agent=ua,
        extra=extra or {},
    )
    try:
        session.add(entry)
        session.commit()
    except Exception:  # noqa: BLE001
        session.rollback()
        log.exception("audit_write_failed action=%s", action)


def list_recent(
    session: Session, *, limit: int = 100, offset: int = 0
) -> list[AuditLog]:
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())  # type: ignore[union-attr]
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(stmt).all())
