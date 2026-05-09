from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=254, index=True, unique=True)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="user", max_length=16)  # "user" | "admin" (Phase 3 swaps to FK)
    # Disabled accounts cannot authenticate; the seeded system user uses this.
    is_active: bool = Field(default=True, nullable=False)
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
    # Bumped on bad login; reset on success. Used for lockout in Phase 3.
    failed_login_count: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
