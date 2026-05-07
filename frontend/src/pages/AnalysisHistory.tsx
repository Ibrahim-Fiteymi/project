import { useMemo, useState } from "react";
import type { AnalysisResponse } from "../api";
import { clearHistory, getHistory, type HistoryEntry } from "../lib/historyStore";
import type { PageKey } from "../layout/Sidebar";

interface Props {
  onSelectResult: (r: AnalysisResponse) => void;
  onNavigate: (page: PageKey) => void;
}

const PLACEHOLDER: HistoryEntry[] = [
  {
    id: "demo-001",
    timestamp: Date.now() - 1000 * 60 * 60 * 24,
    filename: "sample_001.png",
    cellCount: 142,
    mode: "model",
    device: "cpu",
    processingMs: 1820,
    result: null as unknown as AnalysisResponse,
  },
  {
    id: "demo-002",
    timestamp: Date.now() - 1000 * 60 * 60 * 26,
    filename: "sample_002.png",
    cellCount: 87,
    mode: "model",
    device: "cpu",
    processingMs: 1640,
    result: null as unknown as AnalysisResponse,
  },
  {
    id: "demo-003",
    timestamp: Date.now() - 1000 * 60 * 60 * 48,
    filename: "sample_003.jpg",
    cellCount: 211,
    mode: "fallback-demo",
    device: "cpu",
    processingMs: 980,
    result: null as unknown as AnalysisResponse,
  },
];

export default function AnalysisHistory({ onSelectResult, onNavigate }: Props) {
  const [tick, setTick] = useState(0);
  const history = useMemo(() => getHistory(), [tick]);
  const isEmpty = history.length === 0;
  const rows = isEmpty ? PLACEHOLDER : history;

  function handleClear() {
    if (confirm("Clear all history entries from this browser?")) {
      clearHistory();
      setTick((t) => t + 1);
    }
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-head panel-head-row">
          <div>
            <h2 className="panel-title">Recent analyses</h2>
            <p className="panel-sub">
              {isEmpty
                ? "Showing placeholder data — your real analyses will appear here once you run them."
                : `${history.length} entr${history.length === 1 ? "y" : "ies"} stored locally.`}
            </p>
          </div>
          <div className="inline-actions-buttons">
            <button
              type="button"
              className="btn"
              onClick={() => onNavigate("new-analysis")}
            >
              New analysis
            </button>
            {!isEmpty && (
              <button type="button" className="btn-ghost" onClick={handleClear}>
                Clear history
              </button>
            )}
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
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
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
                    <button
                      type="button"
                      className="btn-link"
                      disabled={isEmpty}
                      onClick={() => {
                        if (!isEmpty && row.result) {
                          onSelectResult(row.result);
                          onNavigate("result");
                        }
                      }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
