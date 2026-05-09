/**
 * ProtectedRoute — gate a route on authentication (and optionally on role).
 * Redirects to /login when unauthenticated; to /dashboard when the user is
 * authenticated but lacks the required role.
 */

import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../lib/AuthContext";

interface Props {
  children: ReactNode;
  roles?: string[];
}

export default function ProtectedRoute({ children, roles }: Props) {
  const { user, isAuthenticated, initialising } = useAuth();
  const location = useLocation();

  if (initialising) {
    return (
      <div className="page" role="status" aria-live="polite">
        <div className="panel">Restoring session…</div>
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (roles && roles.length > 0 && (!user || !roles.includes(user.role))) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
