import { NavLink } from "react-router-dom";

import { useAuth } from "../lib/AuthContext";
import { isAdminRole } from "../lib/permissions";

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: "▦" },
  { to: "/new", label: "New Analysis", icon: "＋" },
  { to: "/result", label: "Analysis Result", icon: "◉" },
  { to: "/history", label: "History", icon: "≡" },
  { to: "/reports", label: "Reports", icon: "↗" },
  { to: "/ai-chat", label: "AI Chat", icon: "✦" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

const ADMIN_NAV: NavItem = { to: "/admin", label: "Admin", icon: "✦" };

interface Props {
  onLogout: () => void;
}

export default function Sidebar({ onLogout }: Props) {
  const { user } = useAuth();
  const showAdmin = isAdminRole(user?.role);
  const items = showAdmin ? [...NAV, ADMIN_NAV] : NAV;
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="sidebar-brand">
        <span className="sidebar-brand-mark" aria-hidden>
          ◈
        </span>
        <div>
          <div className="sidebar-brand-title">Nuclei AI</div>
          <div className="sidebar-brand-sub">Microscopy Suite</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-item ${isActive ? "active" : ""}`
            }
          >
            <span className="sidebar-item-icon" aria-hidden>
              {item.icon}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button type="button" className="sidebar-item" onClick={onLogout}>
          <span className="sidebar-item-icon" aria-hidden>
            ⎋
          </span>
          <span>Sign out</span>
        </button>
        <div className="sidebar-version">v0.2 · MVP</div>
      </div>
    </aside>
  );
}
