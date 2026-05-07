import type { ReactNode } from "react";
import type { HealthResponse } from "../api";
import Sidebar, { type PageKey } from "./Sidebar";
import TopHeader from "./TopHeader";

interface Props {
  currentPage: PageKey;
  onNavigate: (page: PageKey) => void;
  onLogout: () => void;
  health: HealthResponse | null;
  userEmail: string | null;
  children: ReactNode;
}

export default function DashboardLayout({
  currentPage,
  onNavigate,
  onLogout,
  health,
  userEmail,
  children,
}: Props) {
  return (
    <div className="layout">
      <Sidebar current={currentPage} onNavigate={onNavigate} onLogout={onLogout} />
      <div className="layout-main">
        <TopHeader page={currentPage} health={health} userEmail={userEmail} />
        <main className="layout-content">{children}</main>
      </div>
    </div>
  );
}
