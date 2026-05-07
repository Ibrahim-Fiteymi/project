import { useEffect, useState } from "react";
import { getHealth, type AnalysisResponse, type HealthResponse } from "./api";
import DashboardLayout from "./layout/DashboardLayout";
import type { PageKey } from "./layout/Sidebar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import NewAnalysis from "./pages/NewAnalysis";
import AnalysisResult from "./pages/AnalysisResult";
import AnalysisHistory from "./pages/AnalysisHistory";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import AiChat from "./pages/AiChat";

export default function App() {
  const [signedIn, setSignedIn] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<PageKey>("dashboard");
  const [latestResult, setLatestResult] = useState<AnalysisResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  function handleSignIn(email: string) {
    setUserEmail(email);
    setSignedIn(true);
    setCurrentPage("dashboard");
  }

  function handleLogout() {
    setSignedIn(false);
    setUserEmail(null);
  }

  function handleAnalysisComplete(r: AnalysisResponse) {
    setLatestResult(r);
  }

  if (!signedIn) {
    return <Login onSignIn={handleSignIn} />;
  }

  let pageNode;
  switch (currentPage) {
    case "dashboard":
      pageNode = <Dashboard health={health} onNavigate={setCurrentPage} />;
      break;
    case "new-analysis":
      pageNode = (
        <NewAnalysis
          onAnalysisComplete={handleAnalysisComplete}
          onNavigate={setCurrentPage}
        />
      );
      break;
    case "result":
      pageNode = <AnalysisResult result={latestResult} onNavigate={setCurrentPage} />;
      break;
    case "history":
      pageNode = (
        <AnalysisHistory
          onSelectResult={setLatestResult}
          onNavigate={setCurrentPage}
        />
      );
      break;
    case "reports":
      pageNode = <Reports />;
      break;
    case "settings":
      pageNode = <Settings userEmail={userEmail} health={health} />;
      break;
    case "ai-chat":
      pageNode = <AiChat />;
      break;
  }

  return (
    <DashboardLayout
      currentPage={currentPage}
      onNavigate={setCurrentPage}
      onLogout={handleLogout}
      health={health}
      userEmail={userEmail}
    >
      {pageNode}
    </DashboardLayout>
  );
}
