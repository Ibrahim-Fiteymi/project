import { useState, type FormEvent } from "react";

interface Props {
  onSignIn: (email: string) => void;
}

export default function Login({ onSignIn }: Props) {
  const [email, setEmail] = useState("demo@nuclei.ai");
  const [password, setPassword] = useState("demo");

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    onSignIn(email.trim());
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
          Visual demo only — no real authentication is performed. Any email will work.
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
            />
          </label>

          <button type="submit" className="btn login-btn">
            Sign in
          </button>
        </form>

        <div className="login-foot">
          <span className="tag">Demo mode</span>
          <span className="metric-caption">No password is checked.</span>
        </div>
      </div>
    </div>
  );
}
