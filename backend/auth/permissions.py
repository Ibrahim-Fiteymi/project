"""Permission constants and the role -> permission matrix.

The matrix is the source of truth for what a role can do; it is seeded into
the `roles` / `permissions` / `role_permissions` tables on first boot so the
admin dashboard reflects the same structure that `require_permission` checks
against. Adding a permission means updating this file *and* re-running
`init_db()` (or the alembic seed migration).
"""

from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    ANALYSIS_CREATE = "analysis:create"
    ANALYSIS_READ_OWN = "analysis:read_own"
    ANALYSIS_READ_ALL = "analysis:read_all"
    ANALYSIS_DELETE_OWN = "analysis:delete_own"
    ANALYSIS_DELETE_ALL = "analysis:delete_all"
    USERS_READ = "users:read"
    USERS_UPDATE = "users:update"
    ROLES_MANAGE = "roles:manage"
    AUDIT_LOGS_READ = "audit_logs:read"


# Canonical role names — kept in sync with /auth/register default and the
# admin role-change validator.
ROLE_RESEARCHER = "researcher"
ROLE_REVIEWER = "reviewer"
ROLE_ADMIN = "admin"
ROLE_SUPERADMIN = "superadmin"

ALL_ROLES: tuple[str, ...] = (
    ROLE_RESEARCHER,
    ROLE_REVIEWER,
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
)


# Inheritance is intentionally NOT modelled — the matrix is enumerated so the
# admin UI can render exactly what's granted without computing closures.
ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    ROLE_RESEARCHER: frozenset({
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ_OWN,
        Permission.ANALYSIS_DELETE_OWN,
    }),
    ROLE_REVIEWER: frozenset({
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ_OWN,
        Permission.ANALYSIS_READ_ALL,
        Permission.ANALYSIS_DELETE_OWN,
    }),
    ROLE_ADMIN: frozenset({
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ_OWN,
        Permission.ANALYSIS_READ_ALL,
        Permission.ANALYSIS_DELETE_OWN,
        Permission.ANALYSIS_DELETE_ALL,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.AUDIT_LOGS_READ,
    }),
    ROLE_SUPERADMIN: frozenset({
        # superadmin has the full matrix plus roles:manage.
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ_OWN,
        Permission.ANALYSIS_READ_ALL,
        Permission.ANALYSIS_DELETE_OWN,
        Permission.ANALYSIS_DELETE_ALL,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.ROLES_MANAGE,
        Permission.AUDIT_LOGS_READ,
    }),
}


def has_permission(role: str | None, permission: Permission) -> bool:
    if not role:
        return False
    return permission in ROLE_PERMISSIONS.get(role, frozenset())


__all__ = [
    "Permission",
    "ROLE_RESEARCHER",
    "ROLE_REVIEWER",
    "ROLE_ADMIN",
    "ROLE_SUPERADMIN",
    "ALL_ROLES",
    "ROLE_PERMISSIONS",
    "has_permission",
]
