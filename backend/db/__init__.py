"""Database package: engine, session, and bootstrap helpers.

Exports:
    engine, get_session — SQLAlchemy engine and FastAPI dependency.
    init_db()           — create tables (SQLite dev) and seed defaults.
    SYSTEM_USER_ID, DEFAULT_PROJECT_ID — fixed IDs used by the MVP.
"""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from backend.auth.permissions import (
    ALL_ROLES,
    ROLE_PERMISSIONS,
    ROLE_SUPERADMIN,
    Permission as PermissionEnum,
)
from backend.db.base import metadata
from backend.db.models import (  # noqa: F401  (registers tables on metadata)
    AnalysisJob,
    AnalysisResult,
    AuditLog,
    PermissionRecord,
    Project,
    RefreshToken,
    Role,
    RolePermission,
    User,
)
from backend.db.session import engine, get_session

log = logging.getLogger(__name__)

SYSTEM_USER_ID = 1
DEFAULT_PROJECT_ID = 1

_SYSTEM_USER_EMAIL = "system@deeply.local"
_DEFAULT_PROJECT_NAME = "Default workspace"


def _seed_roles_and_permissions(session: Session) -> None:
    """Populate the roles, permissions, and role_permissions tables.

    Idempotent: existing rows are preserved, only missing rows are inserted
    and stale role_permission edges (relative to ROLE_PERMISSIONS) are pruned.
    """
    # Permissions first — every code in the enum should have a row.
    code_to_id: dict[str, int] = {}
    for perm in PermissionEnum:
        existing = session.exec(
            select(PermissionRecord).where(PermissionRecord.code == perm.value)
        ).first()
        if existing is None:
            existing = PermissionRecord(code=perm.value, description=perm.name)
            session.add(existing)
            session.flush()
        code_to_id[perm.value] = existing.id  # type: ignore[assignment]

    # Roles — every name in ALL_ROLES should have a row.
    name_to_id: dict[str, int] = {}
    for name in ALL_ROLES:
        existing = session.exec(select(Role).where(Role.name == name)).first()
        if existing is None:
            existing = Role(name=name, description=f"{name.title()} role")
            session.add(existing)
            session.flush()
        name_to_id[name] = existing.id  # type: ignore[assignment]

    # Role-permission edges — re-sync to the matrix. Add missing, remove stale.
    for role_name, perms in ROLE_PERMISSIONS.items():
        role_id = name_to_id[role_name]
        wanted = {code_to_id[p.value] for p in perms}
        current_rows = session.exec(
            select(RolePermission).where(RolePermission.role_id == role_id)
        ).all()
        current_ids = {row.permission_id for row in current_rows}
        for missing_perm_id in wanted - current_ids:
            session.add(
                RolePermission(role_id=role_id, permission_id=missing_perm_id)
            )
        for row in current_rows:
            if row.permission_id not in wanted:
                session.delete(row)

    session.commit()


def _seed_defaults(session: Session) -> None:
    """Create the system user and default project on first boot."""
    user = session.exec(select(User).where(User.email == _SYSTEM_USER_EMAIL)).first()
    if user is None:
        user = User(
            id=SYSTEM_USER_ID,
            email=_SYSTEM_USER_EMAIL,
            password_hash="!disabled",  # placeholder; account is is_active=False
            role=ROLE_SUPERADMIN,
            is_active=False,
        )
        session.add(user)
        session.flush()
    elif user.role != ROLE_SUPERADMIN:
        # Heal pre-RBAC seed where role was "admin" or "user".
        user.role = ROLE_SUPERADMIN
        session.add(user)

    project = session.exec(
        select(Project).where(Project.id == DEFAULT_PROJECT_ID)
    ).first()
    if project is None:
        project = Project(
            id=DEFAULT_PROJECT_ID,
            owner_id=user.id or SYSTEM_USER_ID,
            name=_DEFAULT_PROJECT_NAME,
            description="Auto-created default workspace.",
        )
        session.add(project)

    session.commit()


def init_db() -> None:
    """Create tables and seed defaults. Idempotent."""
    metadata.create_all(engine)
    with Session(engine) as session:
        _seed_roles_and_permissions(session)
        _seed_defaults(session)
    log.info("Database initialised at %s", engine.url)


# Late import to avoid a circular dependency: repositories_auth itself depends
# on backend.db (for the engine + session).
from backend.db import repositories_auth  # noqa: E402, F401


__all__ = [
    "engine",
    "get_session",
    "init_db",
    "SYSTEM_USER_ID",
    "DEFAULT_PROJECT_ID",
    "repositories_auth",
]
