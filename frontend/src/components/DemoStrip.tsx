/** Demo-mode shortcut: load a bundled sample image with one click. */

import { useState } from "react";

interface Sample {
  src: string;
  label: string;
  filename: string;
}

const SAMPLES: Sample[] = [
  { src: "/demo/sample-01.png", label: "Sample 1 — TCGA-18-5592", filename: "sample-01.png" },
  { src: "/demo/sample-02.png", label: "Sample 2 — TCGA-21-5784", filename: "sample-02.png" },
  { src: "/demo/sample-03.png", label: "Sample 3 — TCGA-21-5786", filename: "sample-03.png" },
];

interface Props {
  onSelect: (file: File) => void;
}

async function fetchAsFile(src: string, filename: string): Promise<File> {
  const res = await fetch(src);
  if (!res.ok) throw new Error(`Could not load demo image: ${src}`);
  const blob = await res.blob();
  return new File([blob], filename, { type: blob.type || "image/png" });
}

export default function DemoStrip({ onSelect }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleClick(sample: Sample) {
    setBusy(sample.filename);
    setError(null);
    try {
      const file = await fetchAsFile(sample.src, sample.filename);
      onSelect(file);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="demo-strip" role="region" aria-label="Demo samples">
      <span className="demo-strip-label">No image handy? Try one of these:</span>
      {SAMPLES.map((sample) => (
        <button
          key={sample.filename}
          type="button"
          aria-label={`Load ${sample.label}`}
          title={sample.label}
          disabled={busy !== null}
          onClick={() => handleClick(sample)}
          style={{ background: "none", border: "none", padding: 0 }}
        >
          <img src={sample.src} alt={sample.label} className="demo-thumb" />
        </button>
      ))}
      {busy && <span className="metric-caption">Loading {busy}…</span>}
      {error && <span className="error">{error}</span>}
    </div>
  );
}
