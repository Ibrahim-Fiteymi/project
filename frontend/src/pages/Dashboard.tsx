import { useMemo } from "react";
import type { HealthResponse } from "../api";
import MetricCard from "../components/MetricCard";
import { getHistory } from "../lib/historyStore";
import type { PageKey } from "../layout/Sidebar";

interface Props {
  health: HealthResponse | null;
  onNavigate: (page: PageKey) => void;
}

export default function Dashboard({ health, onNavigate }: Props) {
  const history = useMemo(() => getHistory(), []);
  const total = history.length;
  const completed = history.length;
  const avg =
    history.length === 0
      ? "—"
      : Math.round(
          history.reduce((s, h) => s + h.cellCount, 0) / history.length
        ).toString();

  let modelStatus = "Offline";
  let modelTone: "model" | "fallback" = "fallback";
  let modelCaption = "Backend unreachable";
  if (health) {
    if (health.mode === "model") {
      modelStatus = "Ready";
      modelTone = "model";
      modelCaption = `U-Net loaded · ${health.device}`;
    } else {
      modelStatus = "Degraded";
      modelTone = "fallback";
      modelCaption = `${health.mode} · ${health.device}`;
    }
  }

  return (
    <div className="page">
      <section className="kpi-grid">
        <MetricCard
          label="Total analyses"
          value={total}
          caption={total === 0 ? "No data yet — run your first analysis" : "All sessions"}
        />
        <MetricCard
          label="Completed"
          value={completed}
          caption={completed === 0 ? "—" : "All entries completed successfully"}
        />
        <MetricCard
          label="Avg cell count"
          value={avg}
          caption={history.length === 0 ? "—" : `Across ${history.length} run(s)`}
        />
        <MetricCard
          label="Model status"
          value={modelStatus}
          badge={{ text: modelTone === "model" ? "U-Net" : "fallback", tone: modelTone }}
          caption={modelCaption}
        />
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2 className="panel-title">Quick actions</h2>
          <p className="panel-sub">Jump back into the workflow.</p>
        </div>
        <div className="quick-actions">
          <button type="button" className="btn" onClick={() => onNavigate("new-analysis")}>
            Start a new analysis
          </button>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onNavigate("history")}
          >
            View history
          </button>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onNavigate("reports")}
          >
            Open reports
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2 className="panel-title">Recent activity</h2>
          <p className="panel-sub">
            {history.length === 0
              ? "No runs yet — analyses will appear here as you create them."
              : `Showing the ${Math.min(5, history.length)} most recent run(s).`}
          </p>
        </div>
        {history.length === 0 ? (
          <div className="empty-state">
            <p>Your dashboard is empty.</p>
            <button type="button" className="btn" onClick={() => onNavigate("new-analysis")}>
              Run your first analysis
            </button>
          </div>
        ) : (
          <ul className="recent-list">
            {history.slice(0, 5).map((h) => (
              <li key={h.id} className="recent-item">
                <div>
                  <div className="recent-filename">{h.filename}</div>
                  <div className="metric-caption">
                    {new Date(h.timestamp).toLocaleString()} · {h.processingMs} ms
                  </div>
                </div>
                <div className="recent-count">
                  <span className="metric-value-sm">{h.cellCount}</span>
                  <span className="metric-caption">cells</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
