import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="page">
      <section className="panel">
        <h2 className="panel-title">Page not found</h2>
        <p className="panel-sub">
          The page you tried to open doesn’t exist. It may have been moved or
          renamed.
        </p>
        <Link to="/dashboard" className="btn">
          Back to dashboard
        </Link>
      </section>
    </div>
  );
}
