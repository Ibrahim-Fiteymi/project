/**
 * Backend-backed analysis history.
 *
 * Earlier MVP iterations stored history in `localStorage`. That is now a
 * fallback only — the source of truth is the FastAPI `/api/analyses`
 * endpoint which persists `analysis_jobs` rows in SQLite/Postgres so
 * history survives page refreshes and process restarts.
 */

import {
  AnalysisResponse,
  HistoryItem,
  deleteAnalysis,
  listAnalyses,
} from "../api";

export interface HistoryEntry {
  id: string;
  timestamp: number;
  filename: string;
  cellCount: number;
  mode: string;
  device: string;
  processingMs: number;
  result?: AnalysisResponse;
  raw: HistoryItem;
}

const FALLBACK_KEY = "nuclei.history.fallback.v1";

function toEntry(item: HistoryItem): HistoryEntry {
  return {
    id: item.job_id,
    timestamp: new Date(item.created_at).getTime(),
    filename: item.original_filename ?? `${item.job_id}.png`,
    cellCount: item.cell_count ?? 0,
    mode: item.mode ?? "unknown",
    device: "—",
    processingMs: item.processing_ms ?? 0,
    raw: item,
  };
}

function readFallback(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(FALLBACK_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as HistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeFallback(entries: HistoryEntry[]): void {
  try {
    localStorage.setItem(FALLBACK_KEY, JSON.stringify(entries.slice(0, 50)));
  } catch {
    /* quota / disabled — ignore */
  }
}

/** Fetch the history list from the backend. Falls back to local cache on network error. */
export async function fetchHistory(): Promise<HistoryEntry[]> {
  try {
    const res = await listAnalyses(50, 0);
    const entries = res.items.map(toEntry);
    writeFallback(entries);
    return entries;
  } catch {
    return readFallback();
  }
}

/** Cache an entry locally as soon as a new analysis returns — surfaces in UI before refetch. */
export function cacheLocal(result: AnalysisResponse): HistoryEntry {
  const entry: HistoryEntry = {
    id: result.job_id,
    timestamp: Date.now(),
    filename: result.metadata.original_filename,
    cellCount: result.cell_count,
    mode: result.metadata.mode,
    device: result.metadata.device,
    processingMs: result.metadata.processing_ms,
    result,
    raw: {
      job_id: result.job_id,
      status: result.status,
      cell_count: result.cell_count,
      original_filename: result.metadata.original_filename,
      mode: result.metadata.mode,
      processing_ms: result.metadata.processing_ms,
      input_url: result.input_url,
      mask_url: result.mask_url,
      overlay_url: result.overlay_url,
      threshold: result.metadata.threshold,
      min_area: result.metadata.min_area,
      created_at: new Date().toISOString(),
      finished_at: new Date().toISOString(),
    },
  };
  const next = [entry, ...readFallback().filter((e) => e.id !== entry.id)].slice(0, 50);
  writeFallback(next);
  return entry;
}

export async function removeAnalysis(jobId: string): Promise<void> {
  await deleteAnalysis(jobId);
  writeFallback(readFallback().filter((e) => e.id !== jobId));
}

export function clearLocalCache(): void {
  writeFallback([]);
}
