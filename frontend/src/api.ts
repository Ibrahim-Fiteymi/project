export const API_BASE = "http://127.0.0.1:8080";

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

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}

export async function analyzeImage(file: File): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    let detail = `Analysis failed (${res.status})`;
    try {
      const err = await res.json();
      if (err?.detail) detail = err.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return res.json();
}

export function fileUrl(relative: string): string {
  return `${API_BASE}${relative}`;
}
