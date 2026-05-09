import type { ReactNode } from "react";
import type { HealthResponse } from "../api";
import Sidebar from "./Sidebar";
import TopHeader from "./TopHeader";

interface Props {
  onLogout: () => void;
  health: HealthResponse | null;
  userEmail: string | null;
  children: ReactNode;
}

export default function DashboardLayout({
  onLogout,
  health,
  userEmail,
  children,
}: Props) {
  return (
    <div className="layout">
      <Sidebar onLogout={onLogout} />
      <div className="layout-main">
        <TopHeader health={health} userEmail={userEmail} />
        <main className="layout-content">{children}</main>
      </div>
    </div>
  );
}
