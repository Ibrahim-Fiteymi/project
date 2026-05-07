import { useEffect, useState } from "react";
import { analyzeImage, getHealth, type AnalysisResponse, type HealthResponse } from "./api";
import UploadPanel from "./components/UploadPanel";
import ResultViewer from "./components/ResultViewer";
import WorkflowSteps, { type WorkflowStage } from "./components/WorkflowSteps";

export default function App() {
  const [stage, setStage] = useState<WorkflowStage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function handleFileSelected(f: File) {
    setFile(f);
    setResult(null);
    setError(null);
    setStage("upload");
  }

  async function handleAnalyze() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setStage("segment");
    try {
      const r = await analyzeImage(file);
      setStage("count");
      setResult(r);
      setStage("report");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStage("upload");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <span className="tag">MVP Working Web Prototype</span>
        {health && (
          <span className={`badge ${health.mode === "model" ? "badge-model" : "badge-fallback"}`}>
            backend: {health.mode} · {health.device}
          </span>
        )}
        <h1 style={{ marginTop: 12 }}>
          AI-Powered Microscopy Analysis — Nuclei Segmentation and Cell Counting
        </h1>
        <p>
          Upload one microscopy image. The system runs the trained U-Net, applies connected-component
          post-processing, and returns the predicted mask, the overlay, and an estimated cell count.
        </p>
      </header>

      <section className="panel">
        <WorkflowSteps stage={stage} />
      </section>

      <section className="grid-2">
        <UploadPanel
          file={file}
          previewUrl={previewUrl}
          busy={busy}
          onFileSelected={handleFileSelected}
          onAnalyze={handleAnalyze}
          error={error}
        />
        <ResultViewer result={result} busy={busy} />
      </section>

      <p className="footer-note">
        Local prototype · Backend: FastAPI on http://127.0.0.1:8080 · Frontend: Vite on
        http://127.0.0.1:5173
      </p>
    </div>
  );
}
