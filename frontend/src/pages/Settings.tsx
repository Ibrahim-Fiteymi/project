import type { HealthResponse } from "../api";

interface Props {
  userEmail: string | null;
  health: HealthResponse | null;
}

export default function Settings({ userEmail, health }: Props) {
  return (
    <div className="page">
      <section className="panel settings-section">
        <div className="panel-head">
          <h2 className="panel-title">Profile</h2>
          <p className="panel-sub">Account information for the current demo user.</p>
        </div>
        <div className="settings-grid">
          <label className="field">
            <span className="field-label">Display name</span>
            <input type="text" defaultValue="Demo User" readOnly />
          </label>
          <label className="field">
            <span className="field-label">Email</span>
            <input type="email" defaultValue={userEmail ?? "demo@nuclei.ai"} readOnly />
          </label>
          <label className="field">
            <span className="field-label">Role</span>
            <input type="text" defaultValue="Researcher" readOnly />
          </label>
          <label className="field">
            <span className="field-label">Organisation</span>
            <input type="text" defaultValue="Nuclei AI Lab" readOnly />
          </label>
        </div>
        <p className="metric-caption">Placeholder — profile editing is not implemented in the MVP.</p>
      </section>

      <section className="panel settings-section">
        <div className="panel-head">
          <h2 className="panel-title">Model configuration</h2>
          <p className="panel-sub">Read-only view of the active inference backend.</p>
        </div>
        <div className="settings-grid">
          <label className="field">
            <span className="field-label">Model</span>
            <input type="text" defaultValue="U-Net (nuclei segmentation)" readOnly />
          </label>
          <label className="field">
            <span className="field-label">Mode</span>
            <input type="text" defaultValue={health?.mode ?? "unknown"} readOnly />
          </label>
          <label className="field">
            <span className="field-label">Device</span>
            <input type="text" defaultValue={health?.device ?? "unknown"} readOnly />
          </label>
          <label className="field">
            <span className="field-label">Model loaded</span>
            <input
              type="text"
              defaultValue={health ? (health.model_loaded ? "yes" : "no") : "unknown"}
              readOnly
            />
          </label>
        </div>
        {health?.load_error && (
          <div className="error" role="alert">
            Load error: {health.load_error}
          </div>
        )}
        <p className="metric-caption">
          Placeholder — model selection and threshold tuning are not implemented in the MVP.
        </p>
      </section>

      <section className="panel settings-section">
        <div className="panel-head">
          <h2 className="panel-title">System settings</h2>
          <p className="panel-sub">Application-wide preferences.</p>
        </div>
        <div className="settings-grid">
          <label className="field">
            <span className="field-label">Theme</span>
            <input type="text" defaultValue="3D Glass (dark)" readOnly />
          </label>
          <label className="field">
            <span className="field-label">Backend URL</span>
            <input type="text" defaultValue="http://127.0.0.1:8000" readOnly />
          </label>
          <label className="field">
            <span className="field-label">History retention</span>
            <input type="text" defaultValue="50 entries (local)" readOnly />
          </label>
          <label className="field">
            <span className="field-label">Telemetry</span>
            <input type="text" defaultValue="Disabled" readOnly />
          </label>
        </div>
        <p className="metric-caption">Placeholder — system settings persistence is not implemented in the MVP.</p>
      </section>
    </div>
  );
}
