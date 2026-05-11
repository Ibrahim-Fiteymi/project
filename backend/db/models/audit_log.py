from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    """Append-only audit trail for security-relevant events.

    `actor_user_id` is nullable so we can record events that happen before a
    user exists (e.g. a registration attempt) or anonymous traffic. Payload
    detail goes into the JSON `metadata` blob to stay schema-free.
    """

    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_user_id: Optional[int] = Field(
        default=None, foreign_key="users.id", nullable=True, index=True
    )
    action: str = Field(max_length=64, nullable=False, index=True)
    target_type: Optional[str] = Field(default=None, max_length=32, nullable=True)
    target_id: Optional[str] = Field(default=None, max_length=64, nullable=True)
    ip: Optional[str] = Field(default=None, max_length=64, nullable=True)
    user_agent: Optional[str] = Field(default=None, max_length=255, nullable=True)
    extra: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("extra", JSON, nullable=False, default=dict),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
