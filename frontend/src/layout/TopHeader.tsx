import { useLocation } from "react-router-dom";
import type { HealthResponse } from "../api";
import ThemeToggle from "../components/ThemeToggle";

interface PageMeta {
  title: string;
  subtitle: string;
}

const TITLES: Record<string, PageMeta> = {
  "/dashboard": { title: "Dashboard", subtitle: "Overview of analyses and system status" },
  "/new": { title: "New Analysis", subtitle: "Upload a microscopy image and run nuclei segmentation" },
  "/result": { title: "Analysis Result", subtitle: "Most recent segmentation output" },
  "/history": { title: "Analysis History", subtitle: "Previously processed images" },
  "/reports": { title: "Reports & Export", subtitle: "Export analysis results in different formats" },
  "/settings": { title: "Settings & Admin", subtitle: "Profile, model configuration, and system preferences" },
  "/ai-chat": { title: "AI Chat", subtitle: "Conversational assistant" },
};

interface Props {
  health: HealthResponse | null;
  userEmail: string | null;
}

export default function TopHeader({ health, userEmail }: Props) {
  const { pathname } = useLocation();
  const meta = TITLES[pathname] ?? { title: "Nuclei AI", subtitle: "" };
  const initials = (userEmail ?? "DU").split("@")[0].slice(0, 2).toUpperCase();

  return (
    <header className="top-header">
      <div>
        <h1 className="page-title">{meta.title}</h1>
        <p className="page-subtitle">{meta.subtitle}</p>
      </div>

      <div className="top-header-right">
        {health ? (
          <span
            className={`badge ${health.mode === "model" ? "badge-model" : "badge-fallback"}`}
            title={`device: ${health.device}`}
          >
            backend: {health.mode} · {health.device}
          </span>
        ) : (
          <span className="badge badge-fallback">backend: offline</span>
        )}
        <ThemeToggle />
        <div className="avatar" aria-label={userEmail ?? "Demo user"}>
          {initials}
        </div>
      </div>
    </header>
  );
}
