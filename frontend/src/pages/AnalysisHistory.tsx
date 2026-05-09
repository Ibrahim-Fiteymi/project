import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { AnalysisResponse } from "../api";
import { fileUrl } from "../api";
import { fetchHistory, removeAnalysis, type HistoryEntry } from "../lib/historyStore";

interface Props {
  onSelectResult: (r: AnalysisResponse) => void;
}

function entryToResult(entry: HistoryEntry): AnalysisResponse | null {
  if (entry.result) return entry.result;
  const r = entry.raw;
  if (!r.input_url || !r.mask_url || !r.overlay_url) return null;
  return {
    job_id: r.job_id,
    status: r.status,
    message: "Loaded from history",
    cell_count: r.cell_count ?? 0,
    input_url: r.input_url,
    mask_url: r.mask_url,
    overlay_url: r.overlay_url,
    metadata: {
      original_filename: r.original_filename ?? `${r.job_id}.png`,
      mode: r.mode ?? "unknown",
      threshold: r.threshold,
      min_area: r.min_area ?? 0,
      image_size: 256,
      processing_ms: r.processing_ms ?? 0,
      device: "—",
    },
  };
}

export default function AnalysisHistory({ onSelectResult }: Props) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHistory(await fetchHistory());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const isEmpty = !loading && history.length === 0;

  async function handleDelete(id: string) {
    if (!confirm("Delete this analysis permanently?")) return;
    try {
      await removeAnalysis(id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const sub = useMemo(() => {
    if (loading) return "Loading from server…";
    if (error) return error;
    if (isEmpty) return "No analyses yet — your runs will appear here.";
    return `${history.length} entr${history.length === 1 ? "y" : "ies"} on the server.`;
  }, [loading, error, isEmpty, history.length]);

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-head panel-head-row">
          <div>
            <h2 className="panel-title">Recent analyses</h2>
            <p className="panel-sub">{sub}</p>
          </div>
          <div className="inline-actions-buttons">
            <button type="button" className="btn" onClick={() => navigate("/new")}>
              New analysis
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={refresh}
              disabled={loading}
            >
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>

        <div className="history-table-wrap">
          <table className={`history-table ${isEmpty ? "placeholder" : ""}`}>
            <thead>
              <tr>
                <th>Date</th>
                <th>File</th>
                <th>Cells</th>
                <th>Mode</th>
                <th>Time</th>
                <th>Preview</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.timestamp).toLocaleString()}</td>
                  <td className="mono">{row.filename}</td>
                  <td className="num">{row.cellCount}</td>
                  <td>
                    <span
                      className={`badge ${row.mode === "model" ? "badge-model" : "badge-fallback"}`}
                    >
                      {row.mode}
                    </span>
                  </td>
                  <td className="num">{row.processingMs} ms</td>
                  <td>
                    {row.raw.overlay_url ? (
                      <img
                        src={fileUrl(row.raw.overlay_url)}
                        alt="overlay"
                        className="history-thumb"
                      />
                    ) : (
                      <span className="metric-caption">—</span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn-link"
                      onClick={() => {
                        const result = entryToResult(row);
                        if (result) {
                          onSelectResult(result);
                          navigate("/result");
                        }
                      }}
                    >
                      View
                    </button>
                    <button
                      type="button"
                      className="btn-link danger"
                      onClick={() => handleDelete(row.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {isEmpty && (
                <tr>
                  <td colSpan={7} className="empty-row">
                    No runs yet — start a new analysis to populate this list.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
