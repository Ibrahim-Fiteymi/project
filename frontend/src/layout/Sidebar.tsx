export type PageKey =
  | "dashboard"
  | "new-analysis"
  | "result"
  | "history"
  | "reports"
  | "settings"
  | "ai-chat";

interface NavItem {
  key: PageKey;
  label: string;
  icon: string;
}

const NAV: NavItem[] = [
  { key: "dashboard", label: "Dashboard", icon: "▦" },
  { key: "new-analysis", label: "New Analysis", icon: "＋" },
  { key: "result", label: "Analysis Result", icon: "◉" },
  { key: "history", label: "History", icon: "≡" },
  { key: "reports", label: "Reports", icon: "↗" },
  { key: "ai-chat", label: "AI Chat", icon: "✦" },
  { key: "settings", label: "Settings", icon: "⚙" },
];

interface Props {
  current: PageKey;
  onNavigate: (page: PageKey) => void;
  onLogout: () => void;
}

export default function Sidebar({ current, onNavigate, onLogout }: Props) {
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
        {NAV.map((item) => {
          const active = current === item.key;
          return (
            <button
              key={item.key}
              type="button"
              className={`sidebar-item ${active ? "active" : ""}`}
              onClick={() => onNavigate(item.key)}
              aria-current={active ? "page" : undefined}
            >
              <span className="sidebar-item-icon" aria-hidden>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
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
