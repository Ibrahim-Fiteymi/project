import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../lib/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await register(email.trim(), password);
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

        <h2 className="login-title">Create your workspace</h2>
        <p className="login-subtitle">
          Email + password registration. Your password is hashed with bcrypt.
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
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          <label className="field">
            <span className="field-label">Confirm password</span>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          {error && (
            <div className="alert" role="alert">
              {error}
            </div>
          )}

          <button type="submit" className="btn login-btn" disabled={busy}>
            {busy ? "Creating account…" : "Create account"}
          </button>
        </form>

        <div className="login-foot">
          <span className="metric-caption">
            Already have an account? <Link to="/login">Sign in</Link>
          </span>
        </div>
      </div>
    </div>
  );
}
