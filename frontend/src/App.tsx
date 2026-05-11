/**
 * Top-level router and auth gate.
 *
 * Auth state is owned by AuthProvider (lib/AuthContext). Routes that should
 * only render for signed-in users are wrapped in <ProtectedRoute>. The /login
 * and /register pages are public; everything else lives under the dashboard
 * layout and requires a session.
 */

import { useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { getHealth, type AnalysisResponse, type HealthResponse } from "./api";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./layout/DashboardLayout";
import { useAuth } from "./lib/AuthContext";
import { ROLE_ADMIN, ROLE_SUPERADMIN } from "./lib/permissions";
import Admin from "./pages/Admin";
import AiChat from "./pages/AiChat";
import AnalysisHistory from "./pages/AnalysisHistory";
import AnalysisResult from "./pages/AnalysisResult";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import NewAnalysis from "./pages/NewAnalysis";
import NotFound from "./pages/NotFound";
import Register from "./pages/Register";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

export default function App() {
  const { user, isAuthenticated, logout } = useAuth();
  const [latestResult, setLatestResult] = useState<AnalysisResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const handleLogout = useCallback(async () => {
    await logout();
  }, [logout]);

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />}
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <DashboardLayout
                onLogout={handleLogout}
                health={health}
                userEmail={user?.email ?? ""}
              >
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard health={health} />} />
                  <Route
                    path="/new"
                    element={<NewAnalysis onAnalysisComplete={setLatestResult} />}
                  />
                  <Route
                    path="/result"
                    element={<AnalysisResult result={latestResult} />}
                  />
                  <Route
                    path="/history"
                    element={<AnalysisHistory onSelectResult={setLatestResult} />}
                  />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/ai-chat" element={<AiChat />} />
                  <Route
                    path="/settings"
                    element={
                      <Settings userEmail={user?.email ?? ""} health={health} />
                    }
                  />
                  <Route
                    path="/admin"
                    element={
                      <ProtectedRoute roles={[ROLE_ADMIN, ROLE_SUPERADMIN]}>
                        <Admin />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </DashboardLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
