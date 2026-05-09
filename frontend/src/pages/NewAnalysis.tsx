import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImage, type AnalysisResponse } from "../api";
import UploadPanel from "../components/UploadPanel";
import ResultViewer from "../components/ResultViewer";
import WorkflowSteps, { type WorkflowStage } from "../components/WorkflowSteps";
import DemoStrip from "../components/DemoStrip";
import { cacheLocal } from "../lib/historyStore";

interface Props {
  onAnalysisComplete: (r: AnalysisResponse) => void;
}

export default function NewAnalysis({ onAnalysisComplete }: Props) {
  const [stage, setStage] = useState<WorkflowStage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // Abort any in-flight analysis when the component unmounts.
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  function handleFileSelected(f: File) {
    setFile(f);
    setResult(null);
    setError(null);
    setStage("upload");
  }

  async function handleAnalyze() {
    if (!file) return;
    // Cancel any prior in-flight request before starting a new one.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setBusy(true);
    setError(null);
    setResult(null);
    setStage("segment");
    try {
      const r = await analyzeImage(file, controller.signal);
      setStage("count");
      setResult(r);
      setStage("report");
      cacheLocal(r);
      onAnalysisComplete(r);
    } catch (e) {
      if ((e as { name?: string })?.name === "AbortError") return;
      setError(e instanceof Error ? e.message : String(e));
      setStage("upload");
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <section className="panel">
        <WorkflowSteps stage={stage} />
      </section>

      <DemoStrip onSelect={handleFileSelected} />

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

      {result && (
        <section className="panel inline-actions">
          <div>
            <div className="panel-title">Analysis complete</div>
            <p className="panel-sub">
              Job <code>{result.job_id}</code> · {result.cell_count} cells detected.
            </p>
          </div>
          <div className="inline-actions-buttons">
            <button type="button" className="btn" onClick={() => navigate("/result")}>
              View full result →
            </button>
            <button type="button" className="btn-ghost" onClick={() => navigate("/history")}>
              See history
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
