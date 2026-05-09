import { useNavigate } from "react-router-dom";
import type { AnalysisResponse } from "../api";
import ResultViewer from "../components/ResultViewer";

interface Props {
  result: AnalysisResponse | null;
}

export default function AnalysisResult({ result }: Props) {
  const navigate = useNavigate();

  if (!result) {
    return (
      <div className="page">
        <section className="panel empty-state">
          <h2 className="panel-title">No result yet</h2>
          <p className="panel-sub">
            Run an analysis from the New Analysis page to see segmentation output here.
          </p>
          <button
            type="button"
            className="btn"
            onClick={() => navigate("/new")}
          >
            Go to New Analysis
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-head">
          <h2 className="panel-title">
            Job <code>{result.job_id}</code>
          </h2>
          <p className="panel-sub">
            File: {result.metadata.original_filename} · {result.metadata.processing_ms} ms ·{" "}
            {result.metadata.image_size}×{result.metadata.image_size} ·{" "}
            mode {result.metadata.mode}
          </p>
        </div>
      </section>

      <ResultViewer result={result} busy={false} />

      <section className="panel inline-actions">
        <div>
          <div className="panel-title">Next steps</div>
          <p className="panel-sub">Re-run with a different image or export this result.</p>
        </div>
        <div className="inline-actions-buttons">
          <button type="button" className="btn" onClick={() => navigate("/new")}>
            New analysis
          </button>
          <button type="button" className="btn-ghost" onClick={() => navigate("/reports")}>
            Export
          </button>
        </div>
      </section>
    </div>
  );
}
