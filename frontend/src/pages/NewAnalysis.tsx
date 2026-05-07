import { useEffect, useState } from "react";
import { analyzeImage, type AnalysisResponse } from "../api";
import UploadPanel from "../components/UploadPanel";
import ResultViewer from "../components/ResultViewer";
import WorkflowSteps, { type WorkflowStage } from "../components/WorkflowSteps";
import { addAnalysis } from "../lib/historyStore";
import type { PageKey } from "../layout/Sidebar";

interface Props {
  onAnalysisComplete: (r: AnalysisResponse) => void;
  onNavigate: (page: PageKey) => void;
}

export default function NewAnalysis({ onAnalysisComplete, onNavigate }: Props) {
  const [stage, setStage] = useState<WorkflowStage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
      addAnalysis(r);
      onAnalysisComplete(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStage("upload");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
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

      {result && (
        <section className="panel inline-actions">
          <div>
            <div className="panel-title">Analysis complete</div>
            <p className="panel-sub">
              Job <code>{result.job_id}</code> · {result.cell_count} cells detected.
            </p>
          </div>
          <div className="inline-actions-buttons">
            <button
              type="button"
              className="btn"
              onClick={() => onNavigate("result")}
            >
              View full result →
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => onNavigate("history")}
            >
              See history
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
