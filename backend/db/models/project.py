from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
