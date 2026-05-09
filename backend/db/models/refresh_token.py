from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    """Persisted refresh tokens.

    Only the SHA-256 hash of the raw token is stored. A row exists for the
    lifetime of the token; logout/rotation sets ``revoked_at`` rather than
    deleting, so audit history survives.
    """

    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    token_hash: str = Field(max_length=64, index=True, unique=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)
    user_agent: Optional[str] = Field(default=None, max_length=255, nullable=True)
    ip: Optional[str] = Field(default=None, max_length=64, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
