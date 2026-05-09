/**
 * Deeply Analytics — frontend HTTP client.
 *
 * Centralises all calls to the FastAPI backend so components do not hard-code
 * URLs or parsing. Set `VITE_API_BASE` at build time to point at staging/prod.
 */

export const API_BASE =
  (import.meta.env?.VITE_API_BASE as string | undefined) ?? "http://127.0.0.1:8000";

export interface AnalysisMetadata {
  original_filename: string;
  mode: string;
  threshold: number | null;
  min_area: number;
  image_size: number;
  processing_ms: number;
  device: string;
}

export interface AnalysisResponse {
  job_id: string;
  status: string;
  message: string;
  cell_count: number;
  input_url: string;
  mask_url: string;
  overlay_url: string;
  metadata: AnalysisMetadata;
}

export interface HealthResponse {
  status: string;
  device: string;
  model_loaded: boolean;
  mode: string;
  load_error: string | null;
}

export interface HistoryItem {
  job_id: string;
  status: string;
  cell_count: number | null;
  original_filename: string | null;
  mode: string | null;
  processing_ms: number | null;
  input_url: string | null;
  mask_url: string | null;
  overlay_url: string | null;
  threshold: number | null;
  min_area: number | null;
  created_at: string;
  finished_at: string | null;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
}

async function parseError(res: Response, fallback: string): Promise<string> {
  try {
    const err = (await res.json()) as { detail?: string };
    if (err?.detail) return err.detail;
  } catch {
    /* ignore */
  }
  return fallback;
}

// Lazy-imported to avoid a circular dep (auth.ts imports API_BASE from here).
async function authedFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const { tokens, refreshIfPossible } = await import("./lib/auth");
  const access = tokens.access();
  const headers = new Headers(init.headers ?? {});
  if (access) headers.set("Authorization", `Bearer ${access}`);
  let res = await fetch(input, { ...init, headers });
  if (res.status !== 401) return res;
  // One refresh-then-retry attempt; if refresh fails we clear tokens and the
  // caller surfaces the 401 to the AuthProvider, which routes to /login.
  const refreshed = await refreshIfPossible();
  if (!refreshed) return res;
  const retryHeaders = new Headers(init.headers ?? {});
  retryHeaders.set("Authorization", `Bearer ${refreshed.access_token}`);
  res = await fetch(input, { ...init, headers: retryHeaders });
  return res;
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { signal });
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}

export async function analyzeImage(
  file: File,
  signal?: AbortSignal,
): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await authedFetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: form,
    signal,
  });
  if (!res.ok) {
    throw new Error(await parseError(res, `Analysis failed (${res.status})`));
  }
  return res.json();
}

export async function listAnalyses(
  limit = 50,
  offset = 0,
  signal?: AbortSignal,
): Promise<HistoryResponse> {
  const res = await authedFetch(
    `${API_BASE}/api/analyses?limit=${limit}&offset=${offset}`,
    { signal },
  );
  if (!res.ok) throw new Error(await parseError(res, `History fetch failed (${res.status})`));
  return res.json();
}

export async function getAnalysis(jobId: string, signal?: AbortSignal): Promise<HistoryItem> {
  const res = await authedFetch(
    `${API_BASE}/api/analyses/${encodeURIComponent(jobId)}`,
    { signal },
  );
  if (!res.ok) throw new Error(await parseError(res, `Analysis not found (${res.status})`));
  return res.json();
}

export async function deleteAnalysis(jobId: string, signal?: AbortSignal): Promise<void> {
  const res = await authedFetch(`${API_BASE}/api/analyses/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    signal,
  });
  if (!res.ok) throw new Error(await parseError(res, `Delete failed (${res.status})`));
}

export function fileUrl(relative: string | null | undefined): string {
  if (!relative) return "";
  return `${API_BASE}${relative}`;
}
