import type { AnalysisResponse } from "../api";

const STORAGE_KEY = "nuclei.history.v1";
const MAX_ENTRIES = 50;

export interface HistoryEntry {
  id: string;
  timestamp: number;
  filename: string;
  cellCount: number;
  mode: string;
  device: string;
  processingMs: number;
  result: AnalysisResponse;
}

function read(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as HistoryEntry[]) : [];
  } catch {
    return [];
  }
}

function write(entries: HistoryEntry[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    /* quota or disabled — silently ignore in MVP */
  }
}

export function getHistory(): HistoryEntry[] {
  return read().sort((a, b) => b.timestamp - a.timestamp);
}

export function addAnalysis(result: AnalysisResponse): HistoryEntry {
  const entry: HistoryEntry = {
    id: result.job_id,
    timestamp: Date.now(),
    filename: result.metadata.original_filename,
    cellCount: result.cell_count,
    mode: result.metadata.mode,
    device: result.metadata.device,
    processingMs: result.metadata.processing_ms,
    result,
  };
  const next = [entry, ...read().filter((e) => e.id !== entry.id)].slice(0, MAX_ENTRIES);
  write(next);
  return entry;
}

export function clearHistory(): void {
  write([]);
}
