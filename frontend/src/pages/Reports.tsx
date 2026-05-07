interface ExportCard {
  format: string;
  title: string;
  description: string;
  icon: string;
}

const EXPORTS: ExportCard[] = [
  {
    format: "CSV",
    title: "Export as CSV",
    description:
      "Tabular export of all analyses with cell counts, timestamps, processing time, and mode.",
    icon: "▤",
  },
  {
    format: "PNG",
    title: "Export overlays as PNG",
    description:
      "Bundle the original, mask, and overlay images for the most recent analyses.",
    icon: "🖼",
  },
  {
    format: "PDF",
    title: "Export report as PDF",
    description:
      "Printable summary report with images, KPIs, and a metadata appendix.",
    icon: "▦",
  },
];

export default function Reports() {
  return (
    <div className="page">
      <section className="panel">
        <div className="panel-head">
          <h2 className="panel-title">Export your analyses</h2>
          <p className="panel-sub">
            Download analysis data and result imagery in your preferred format.
          </p>
        </div>

        <div className="report-grid">
          {EXPORTS.map((e) => (
            <div key={e.format} className="card report-card">
              <div className="report-card-icon" aria-hidden>
                {e.icon}
              </div>
              <h4 className="report-card-title">{e.title}</h4>
              <p className="report-card-desc">{e.description}</p>
              <div className="report-card-footer">
                <span className="tag">Coming soon</span>
                <button type="button" className="btn-ghost" disabled>
                  Export {e.format}
                </button>
              </div>
            </div>
          ))}
        </div>

        <p className="metric-caption" style={{ marginTop: 16 }}>
          Placeholder — export endpoints are not implemented in the MVP.
        </p>
      </section>
    </div>
  );
}
