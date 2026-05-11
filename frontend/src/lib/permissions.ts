/**
 * Frontend mirror of backend.auth.permissions.
 *
 * The backend is the authoritative gate (every protected route checks
 * server-side). This file exists ONLY to drive UI affordances — hiding nav
 * items the user cannot use, disabling buttons, etc. Do not treat it as a
 * security boundary.
 *
 * Keep ROLE_PERMISSIONS in sync with backend/auth/permissions.py manually
 * (or write a generator later). When in doubt, the server is right.
 */

export const Permission = {
  ANALYSIS_CREATE: "analysis:create",
  ANALYSIS_READ_OWN: "analysis:read_own",
  ANALYSIS_READ_ALL: "analysis:read_all",
  ANALYSIS_DELETE_OWN: "analysis:delete_own",
  ANALYSIS_DELETE_ALL: "analysis:delete_all",
  USERS_READ: "users:read",
  USERS_UPDATE: "users:update",
  ROLES_MANAGE: "roles:manage",
  AUDIT_LOGS_READ: "audit_logs:read",
} as const;

export type PermissionCode = (typeof Permission)[keyof typeof Permission];

export const ROLE_RESEARCHER = "researcher";
export const ROLE_REVIEWER = "reviewer";
export const ROLE_ADMIN = "admin";
export const ROLE_SUPERADMIN = "superadmin";

export const ALL_ROLES = [
  ROLE_RESEARCHER,
  ROLE_REVIEWER,
  ROLE_ADMIN,
  ROLE_SUPERADMIN,
] as const;

export type Role = (typeof ALL_ROLES)[number];

const ROLE_PERMISSIONS: Record<string, ReadonlySet<PermissionCode>> = {
  [ROLE_RESEARCHER]: new Set([
    Permission.ANALYSIS_CREATE,
    Permission.ANALYSIS_READ_OWN,
    Permission.ANALYSIS_DELETE_OWN,
  ]),
  [ROLE_REVIEWER]: new Set([
    Permission.ANALYSIS_CREATE,
    Permission.ANALYSIS_READ_OWN,
    Permission.ANALYSIS_READ_ALL,
    Permission.ANALYSIS_DELETE_OWN,
  ]),
  [ROLE_ADMIN]: new Set([
    Permission.ANALYSIS_CREATE,
    Permission.ANALYSIS_READ_OWN,
    Permission.ANALYSIS_READ_ALL,
    Permission.ANALYSIS_DELETE_OWN,
    Permission.ANALYSIS_DELETE_ALL,
    Permission.USERS_READ,
    Permission.USERS_UPDATE,
    Permission.AUDIT_LOGS_READ,
  ]),
  [ROLE_SUPERADMIN]: new Set([
    Permission.ANALYSIS_CREATE,
    Permission.ANALYSIS_READ_OWN,
    Permission.ANALYSIS_READ_ALL,
    Permission.ANALYSIS_DELETE_OWN,
    Permission.ANALYSIS_DELETE_ALL,
    Permission.USERS_READ,
    Permission.USERS_UPDATE,
    Permission.ROLES_MANAGE,
    Permission.AUDIT_LOGS_READ,
  ]),
};

export function hasPermission(
  role: string | null | undefined,
  permission: PermissionCode,
): boolean {
  if (!role) return false;
  return ROLE_PERMISSIONS[role]?.has(permission) ?? false;
}

export function isAdminRole(role: string | null | undefined): boolean {
  return role === ROLE_ADMIN || role === ROLE_SUPERADMIN;
}
