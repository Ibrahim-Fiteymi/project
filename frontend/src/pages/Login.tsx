import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../lib/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setError(null);
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card panel">
        <div className="login-brand">
          <span className="sidebar-brand-mark" aria-hidden>
            ◈
          </span>
          <div>
            <div className="sidebar-brand-title">Nuclei AI</div>
            <div className="sidebar-brand-sub">Microscopy Suite</div>
          </div>
        </div>

        <h2 className="login-title">Sign in to your workspace</h2>
        <p className="login-subtitle">
          Email and password authentication. Sessions are protected with JWTs.
        </p>

        <form onSubmit={handleSubmit} className="login-form">
          <label className="field">
            <span className="field-label">Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label className="field">
            <span className="field-label">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && (
            <div className="alert" role="alert">
              {error}
            </div>
          )}

          <button type="submit" className="btn login-btn" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="login-foot">
          <span className="metric-caption">
            Need an account? <Link to="/register">Create one</Link>
          </span>
        </div>
      </div>
    </div>
  );
}
