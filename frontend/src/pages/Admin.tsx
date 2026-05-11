import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  adminChangeUserActive,
  adminChangeUserRole,
  adminListAuditLogs,
  adminListUsers,
  type AdminUser,
  type AuditLogEntry,
} from "../api";
import { useAuth } from "../lib/AuthContext";
import { ALL_ROLES, ROLE_SUPERADMIN, isAdminRole } from "../lib/permissions";

type Tab = "users" | "audit";

export default function Admin() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("users");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refreshTick = useRef(0);

  const isSuperadmin = user?.role === ROLE_SUPERADMIN;

  const refresh = useCallback(async () => {
    refreshTick.current += 1;
    const tick = refreshTick.current;
    setLoading(true);
    setError(null);
    try {
      if (tab === "users") {
        const list = await adminListUsers(100);
        if (tick !== refreshTick.current) return;
        setUsers(list.items);
      } else {
        const list = await adminListAuditLogs(100);
        if (tick !== refreshTick.current) return;
        setLogs(list.items);
      }
    } catch (e) {
      if (tick !== refreshTick.current) return;
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (tick === refreshTick.current) setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleRoleChange(target: AdminUser, nextRole: string) {
    if (nextRole === target.role) return;
    setError(null);
    try {
      const updated = await adminChangeUserRole(target.id, nextRole);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleActiveToggle(target: AdminUser) {
    setError(null);
    try {
      const updated = await adminChangeUserActive(target.id, !target.is_active);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-title">Administration</div>
        <p className="panel-sub">
          Signed in as <code>{user?.email}</code> ({user?.role}).
          {!isSuperadmin && " Some role changes require superadmin."}
        </p>
        <div className="inline-actions-buttons" style={{ marginTop: 12 }}>
          <button
            type="button"
            className={tab === "users" ? "btn" : "btn-ghost"}
            onClick={() => setTab("users")}
          >
            Users
          </button>
          <button
            type="button"
            className={tab === "audit" ? "btn" : "btn-ghost"}
            onClick={() => setTab("audit")}
          >
            Audit log
          </button>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => void refresh()}
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>

        {error && (
          <div className="alert" role="alert" style={{ marginTop: 12 }}>
            {error}
          </div>
        )}
      </section>

      {tab === "users" ? (
        <UsersTable
          users={users}
          currentUserId={user?.id ?? null}
          onChangeRole={handleRoleChange}
          onToggleActive={handleActiveToggle}
        />
      ) : (
        <AuditLogTable logs={logs} />
      )}
    </div>
  );
}

interface UsersTableProps {
  users: AdminUser[];
  currentUserId: number | null;
  onChangeRole: (u: AdminUser, role: string) => void | Promise<void>;
  onToggleActive: (u: AdminUser) => void | Promise<void>;
}

function UsersTable({
  users,
  currentUserId,
  onChangeRole,
  onToggleActive,
}: UsersTableProps) {
  return (
    <section className="panel">
      <div className="panel-title">Users</div>
      <p className="panel-sub">{users.length} loaded.</p>
      <table className="data-table" style={{ width: "100%", marginTop: 12 }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last login</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.email}</td>
              <td>
                <select
                  aria-label={`Role for ${u.email}`}
                  value={u.role}
                  onChange={(e) => void onChangeRole(u, e.target.value)}
                  disabled={u.id === currentUserId}
                >
                  {ALL_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <span className={u.is_active ? "tag tag-ok" : "tag tag-warn"}>
                  {u.is_active ? "active" : "disabled"}
                </span>
              </td>
              <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "—"}</td>
              <td>
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => void onToggleActive(u)}
                  disabled={u.id === currentUserId}
                >
                  {u.is_active ? "Deactivate" : "Activate"}
                </button>
              </td>
            </tr>
          ))}
          {users.length === 0 && (
            <tr>
              <td colSpan={6} className="empty">
                No users yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}

function AuditLogTable({ logs }: { logs: AuditLogEntry[] }) {
  const formatted = useMemo(
    () =>
      logs.map((log) => ({
        ...log,
        when: new Date(log.created_at).toLocaleString(),
        extraText: Object.keys(log.extra ?? {}).length
          ? JSON.stringify(log.extra)
          : "",
      })),
    [logs],
  );

  return (
    <section className="panel">
      <div className="panel-title">Audit log</div>
      <p className="panel-sub">{logs.length} most-recent entries.</p>
      <table className="data-table" style={{ width: "100%", marginTop: 12 }}>
        <thead>
          <tr>
            <th>When</th>
            <th>Actor</th>
            <th>Action</th>
            <th>Target</th>
            <th>IP</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>
          {formatted.map((log) => (
            <tr key={log.id}>
              <td>{log.when}</td>
              <td>{log.actor_user_id ?? "—"}</td>
              <td>
                <code>{log.action}</code>
              </td>
              <td>
                {log.target_type ? `${log.target_type}/${log.target_id ?? "—"}` : "—"}
              </td>
              <td>{log.ip ?? "—"}</td>
              <td>
                <code className="audit-extra">{log.extraText}</code>
              </td>
            </tr>
          ))}
          {logs.length === 0 && (
            <tr>
              <td colSpan={6} className="empty">
                No audit events yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}

// Re-export so callers (Sidebar, App router) can keep all admin-gating in one place.
export { isAdminRole };
