from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=32, index=True, unique=True, nullable=False)
    description: Optional[str] = Field(default=None, max_length=255, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Stored as the string value of the Permission enum (e.g. "analysis:create").
    code: str = Field(max_length=64, index=True, unique=True, nullable=False)
    description: Optional[str] = Field(default=None, max_length=255, nullable=True)


class RolePermission(SQLModel, table=True):
    """Join table between roles and permissions.

    Composite primary key — each (role, permission) pair is unique by definition.
    """

    __tablename__ = "role_permissions"

    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
