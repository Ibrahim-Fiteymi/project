"""Build the Phase 1 Software Architecture Document (SAD v1) PDF.

Renders four UML-style diagrams as PNGs (matplotlib) and assembles the SAD
document with reportlab. Output: docs/Phase1_SAD_v1.pdf.

Run from the project root:
    python scripts/build_sad_phase1.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "docs" / "diagrams"
PDF_OUT = ROOT / "docs" / "Phase1_SAD_v1.pdf"
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Diagram rendering (matplotlib -> PNG)
# =============================================================================

def _save(fig, name: str) -> Path:
    out = DIAGRAMS_DIR / name
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def draw_use_case_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # System boundary
    boundary = patches.FancyBboxPatch(
        (2.6, 0.6), 5.8, 5.8,
        boxstyle="round,pad=0.05,rounding_size=0.1",
        linewidth=1.5, edgecolor="#1f4e79", facecolor="#f2f6fb",
    )
    ax.add_patch(boundary)
    ax.text(5.5, 6.15, "Deeply Analytics — Nuclei Analysis System",
            ha="center", fontsize=11, weight="bold", color="#1f4e79")

    # Use cases (ovals) inside the boundary
    use_cases = [
        ("UC-1\nUpload microscopy image", 5.5, 5.2),
        ("UC-2\nRun nuclei analysis", 5.5, 4.1),
        ("UC-3\nView analysis result", 5.5, 3.0),
        ("UC-4\nDownload mask / overlay", 5.5, 1.9),
        ("UC-5\nCheck system health", 5.5, 0.95),
    ]
    uc_centers = []
    for label, x, y in use_cases:
        ell = patches.Ellipse((x, y), 3.4, 0.7,
                              edgecolor="#2c5f8d", facecolor="#dde8f4",
                              linewidth=1.2)
        ax.add_patch(ell)
        ax.text(x, y, label, ha="center", va="center", fontsize=8.5)
        uc_centers.append((x, y))

    # Actors (stick figures)
    def actor(ax, x, y, label):
        ax.plot([x], [y + 0.35], marker="o", markersize=10,
                markerfacecolor="white", markeredgecolor="#222")
        ax.plot([x, x], [y + 0.30, y - 0.10], color="#222")
        ax.plot([x - 0.25, x + 0.25], [y + 0.10, y + 0.10], color="#222")
        ax.plot([x, x - 0.20], [y - 0.10, y - 0.40], color="#222")
        ax.plot([x, x + 0.20], [y - 0.10, y - 0.40], color="#222")
        ax.text(x, y - 0.65, label, ha="center", va="top", fontsize=9, weight="bold")

    actor(ax, 1.0, 5.2, "Researcher")
    actor(ax, 1.0, 3.0, "Lab Technician")
    actor(ax, 10.0, 1.0, "Admin /\nMonitoring")

    # Associations: actor -> use case
    def assoc(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-", color="#444", lw=1.0))

    # Researcher -> UC-1, UC-2, UC-3, UC-4
    for ux, uy in [uc_centers[0], uc_centers[1], uc_centers[2], uc_centers[3]]:
        assoc(1.25, 5.05, ux - 1.7, uy)
    # Lab Tech -> UC-1, UC-3
    assoc(1.25, 3.0, uc_centers[0][0] - 1.7, uc_centers[0][1])
    assoc(1.25, 3.0, uc_centers[2][0] - 1.7, uc_centers[2][1])
    # Admin -> UC-5
    assoc(9.75, 1.0, uc_centers[4][0] + 1.7, uc_centers[4][1])

    ax.text(5.5, 0.15, "Figure 3.1 — Use Case Diagram",
            ha="center", fontsize=9, style="italic", color="#555")

    return _save(fig, "use_case_diagram.png")


def draw_logical_view_class_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")

    def box(x, y, w, h, title, body, proposed=False):
        ls = "--" if proposed else "-"
        edge = "#9a3a3a" if proposed else "#1f4e79"
        face = "#fbeeee" if proposed else "#eaf2fb"
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            linewidth=1.4, edgecolor=edge, facecolor=face, linestyle=ls,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.25, title,
                ha="center", va="top", fontsize=9.5, weight="bold", color=edge)
        ax.plot([x + 0.05, x + w - 0.05], [y + h - 0.45, y + h - 0.45],
                color=edge, lw=0.8)
        ax.text(x + 0.12, y + h - 0.6, body, ha="left", va="top",
                fontsize=7.8, color="#222")
        if proposed:
            ax.text(x + w - 0.05, y + 0.05, "[Proposed]",
                    ha="right", va="bottom", fontsize=6.5,
                    style="italic", color=edge)

    # Frontend
    box(0.2, 6.4, 3.4, 1.4, "React UI (frontend/)",
        "+ App.tsx\n+ UploadPanel.tsx\n+ ResultViewer.tsx\n+ api.ts (fetch)")

    # FastAPI
    box(4.2, 6.4, 3.4, 1.4, "FastAPI App (backend/main.py)",
        "+ GET  /api/health\n+ POST /api/analyze\n+ GET  /files/{name}\n+ CORSMiddleware")

    # Schemas
    box(8.2, 6.4, 3.6, 1.4, "Pydantic Schemas (schemas.py)",
        "HealthResponse\nAnalysisMetadata\nAnalysisResponse")

    # AnalysisService
    box(2.2, 4.3, 3.6, 1.5, "AnalysisService (services/)",
        "+ analyze(bytes, name)\n+ get_health()\n- _ensure_model_loaded()\n- _decode_image()\n- _predict_with_model() / _predict_fallback()")

    # Config
    box(6.4, 4.3, 3.4, 1.5, "Settings (config.py)",
        "env, allowed_origins\nstorage_root, threshold\nmodel_checkpoint, image_size\nmax_upload_bytes")

    # U-Net
    box(0.2, 2.2, 3.0, 1.5, "U-Net Model (PyTorch)",
        "smp.Unet(\n  encoder=resnet18,\n  classes=1,\n  in_channels=3)\nsigmoid > 0.8 -> mask")

    # OpenCV / postprocess
    box(3.6, 2.2, 3.0, 1.5, "OpenCV / Postprocess",
        "cv2.imdecode / resize\nmake_overlay()\ncount_nuclei_from_binary()\n(connected components)")

    # Storage
    box(7.0, 2.2, 2.6, 1.5, "Storage (FS)",
        "uploads/{job}.png\nresults/{job}_input.png\nresults/{job}_mask.png\nresults/{job}_overlay.png")

    # Proposed DB
    box(0.2, 0.2, 2.6, 1.5, "User", "id, email\npassword_hash\nrole, created_at",
        proposed=True)
    box(3.0, 0.2, 2.6, 1.5, "Project", "id, owner_id\nname, description\ncreated_at",
        proposed=True)
    box(5.8, 0.2, 2.8, 1.5, "AnalysisJob",
        "id, project_id, owner_id\nstatus, input_path\nparameters (JSONB)\nstarted_at, finished_at",
        proposed=True)
    box(8.8, 0.2, 3.0, 1.5, "AnalysisResult",
        "id, job_id, cell_count\nmode, mask_path\noverlay_path, density_path\nprocessing_ms",
        proposed=True)

    # Dependencies (arrows)
    def dep(x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.0))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.05, label,
                    ha="center", fontsize=7, color="#555")

    # React UI -> FastAPI
    dep(3.6, 7.1, 4.2, 7.1, "HTTPS")
    # FastAPI -> Schemas
    dep(7.6, 7.1, 8.2, 7.1)
    # FastAPI -> AnalysisService
    dep(5.9, 6.4, 4.2, 5.8)
    # AnalysisService -> Settings
    dep(5.8, 5.0, 6.4, 5.0)
    # AnalysisService -> U-Net
    dep(2.6, 4.3, 1.7, 3.7)
    # AnalysisService -> OpenCV
    dep(4.0, 4.3, 5.1, 3.7)
    # AnalysisService -> Storage
    dep(5.1, 4.3, 8.0, 3.7)
    # FastAPI -> Storage (FileResponse)
    dep(7.0, 6.4, 8.2, 3.7)
    # AnalysisJob -> User
    dep(5.8, 0.95, 2.8, 0.95)
    # AnalysisJob -> Project
    dep(5.8, 0.6, 5.6, 0.6)
    # AnalysisResult -> AnalysisJob
    dep(8.8, 0.95, 8.6, 0.95)

    # Legend
    leg_x, leg_y = 0.3, 7.95
    ax.text(leg_x, leg_y, "Solid border = implemented today    ",
            fontsize=8, color="#1f4e79")
    ax.text(leg_x + 4.2, leg_y, "Dashed border = proposed (Phase 2)",
            fontsize=8, color="#9a3a3a", style="italic")

    return _save(fig, "logical_view_class_diagram.png")


def draw_sequence_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(12, 8.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")

    actors = ["User", "React UI", "FastAPI\nRouter", "AnalysisService",
              "U-Net Model", "OpenCV\n+ counter", "Filesystem"]
    n = len(actors)
    xs = [1.0 + i * 1.65 for i in range(n)]
    head_y = 8.4
    bottom_y = 0.6

    for x, name in zip(xs, actors):
        head = patches.FancyBboxPatch(
            (x - 0.65, head_y - 0.35), 1.3, 0.6,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            linewidth=1.2, edgecolor="#1f4e79", facecolor="#dde8f4",
        )
        ax.add_patch(head)
        ax.text(x, head_y - 0.05, name, ha="center", va="center",
                fontsize=8.5, weight="bold")
        ax.plot([x, x], [head_y - 0.35, bottom_y], color="#888",
                lw=0.8, linestyle=(0, (3, 3)))

    def message(src, dst, y, label, dashed=False):
        x1, x2 = xs[src], xs[dst]
        style = "->,head_length=4,head_width=3" if not dashed else "->,head_length=4,head_width=3"
        ls = "-" if not dashed else (0, (4, 2))
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="->", color="#222",
                                    lw=1.1, linestyle=ls))
        # label centered slightly above the arrow
        ax.text((x1 + x2) / 2, y + 0.08, label,
                ha="center", va="bottom", fontsize=7.8, color="#222")

    def selfmsg(src, y, label):
        x = xs[src]
        ax.annotate("", xy=(x + 0.5, y - 0.2), xytext=(x + 0.5, y),
                    arrowprops=dict(arrowstyle="->", color="#222", lw=1.0))
        ax.plot([x, x + 0.5, x + 0.5], [y, y, y - 0.2], color="#222", lw=1.0)
        ax.text(x + 0.6, y - 0.1, label, ha="left", va="center", fontsize=7.8)

    # Messages (top to bottom)
    y = 7.7
    step = 0.55
    message(0, 1, y, "Drag-drop image + click Run analysis"); y -= step
    message(1, 2, y, "POST /api/analyze (multipart)"); y -= step
    selfmsg(2, y, "Validate content_type, size"); y -= step
    message(2, 3, y, "analyze(bytes, filename)"); y -= step
    selfmsg(3, y, "_ensure_model_loaded() (lazy)"); y -= step
    selfmsg(3, y, "_decode_image -> RGB 256x256"); y -= step
    message(3, 4, y, "predict(tensor)"); y -= step
    message(4, 3, y, "logits -> sigmoid > 0.8 -> mask", dashed=True); y -= step
    message(3, 5, y, "make_overlay + count_nuclei"); y -= step
    message(5, 3, y, "overlay, cell_count", dashed=True); y -= step
    message(3, 6, y, "save input/mask/overlay PNGs"); y -= step
    message(3, 2, y, "AnalysisResult dataclass", dashed=True); y -= step
    message(2, 1, y, "200 OK · AnalysisResponse JSON", dashed=True); y -= step
    message(1, 0, y, "Render result tiles + cell count", dashed=True)

    ax.text(6, 0.15, "Figure 5.1 — Sequence Diagram: POST /api/analyze",
            ha="center", fontsize=9, style="italic", color="#555")

    return _save(fig, "process_view_sequence.png")


def draw_activity_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(7.5, 11))
    ax.set_xlim(0, 7.5)
    ax.set_ylim(0, 13)
    ax.axis("off")

    def node(y, text, w=4.0, kind="action"):
        x = (7.5 - w) / 2
        if kind == "action":
            patch = patches.FancyBboxPatch(
                (x, y), w, 0.7,
                boxstyle="round,pad=0.02,rounding_size=0.25",
                linewidth=1.2, edgecolor="#1f4e79", facecolor="#dde8f4",
            )
        elif kind == "decision":
            cx, cy = 3.75, y + 0.45
            patch = patches.Polygon(
                [[cx, cy + 0.55], [cx + 1.4, cy], [cx, cy - 0.55], [cx - 1.4, cy]],
                closed=True, linewidth=1.2,
                edgecolor="#9a6a1f", facecolor="#fff2dd",
            )
        elif kind == "start":
            patch = patches.Circle((3.75, y + 0.35), 0.22,
                                   linewidth=1.0, edgecolor="#222", facecolor="#222")
        elif kind == "end":
            patch = patches.Circle((3.75, y + 0.35), 0.27,
                                   linewidth=1.5, edgecolor="#222", facecolor="white")
            ax.add_patch(patch)
            patch = patches.Circle((3.75, y + 0.35), 0.13,
                                   linewidth=1.0, edgecolor="#222", facecolor="#222")
        ax.add_patch(patch)
        if kind in ("action", "decision"):
            ax.text(3.75, y + 0.35, text, ha="center", va="center",
                    fontsize=8.3, color="#111")

    def arrow(y1, y2, label=""):
        ax.annotate("", xy=(3.75, y2), xytext=(3.75, y1),
                    arrowprops=dict(arrowstyle="->", color="#444", lw=1.0))
        if label:
            ax.text(3.95, (y1 + y2) / 2, label, ha="left", va="center",
                    fontsize=7.5, color="#444")

    # Layout from top to bottom
    y = 12.2
    node(y, "", kind="start"); top = y; y -= 0.9
    node(y, "Receive POST /api/analyze (file)"); arrow(top + 0.35, y + 0.7); top = y; y -= 1.0
    node(y, "Validate MIME type and size"); arrow(top, y + 0.7); top = y; y -= 1.0
    node(y, "Lazy-load U-Net checkpoint"); arrow(top, y + 0.7); top = y; y -= 1.0
    node(y, "Decode + resize image to 256×256"); arrow(top, y + 0.7); top = y; y -= 1.4
    node(y, "Model loaded?", kind="decision"); arrow(top, y + 0.9); top_dec = y; y -= 1.3

    # Two branches: Yes (left) / No (right)
    # Yes branch (model)
    yes_x = 1.6
    no_x = 5.9
    # Yes path
    ax.annotate("", xy=(yes_x + 1.2, y + 0.7), xytext=(3.75 - 1.4, top_dec + 0.45),
                arrowprops=dict(arrowstyle="->", color="#444", lw=1.0))
    ax.text(2.2, top_dec + 0.55, "yes", fontsize=7.5, color="#444")
    rect_y = patches.FancyBboxPatch(
        (yes_x, y), 2.4, 0.7,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=1.2, edgecolor="#1f4e79", facecolor="#dde8f4",
    )
    ax.add_patch(rect_y)
    ax.text(yes_x + 1.2, y + 0.35, "U-Net forward + sigmoid > 0.8",
            ha="center", va="center", fontsize=8.3)

    # No path
    ax.annotate("", xy=(no_x + 0.7, y + 0.7), xytext=(3.75 + 1.4, top_dec + 0.45),
                arrowprops=dict(arrowstyle="->", color="#444", lw=1.0))
    ax.text(5.0, top_dec + 0.55, "no", fontsize=7.5, color="#444")
    rect_n = patches.FancyBboxPatch(
        (no_x - 0.5, y), 2.4, 0.7,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=1.2, edgecolor="#9a6a1f", facecolor="#fff2dd",
    )
    ax.add_patch(rect_n)
    ax.text(no_x + 0.7, y + 0.35, "Otsu fallback (demo)",
            ha="center", va="center", fontsize=8.3)

    branch_y = y
    y -= 0.9
    # Merge
    ax.annotate("", xy=(3.75, y + 0.4), xytext=(yes_x + 1.2, branch_y),
                arrowprops=dict(arrowstyle="->", color="#444", lw=1.0))
    ax.annotate("", xy=(3.75, y + 0.4), xytext=(no_x + 0.7, branch_y),
                arrowprops=dict(arrowstyle="->", color="#444", lw=1.0))

    node(y, "Threshold mask + connected components"); top = y; y -= 1.0
    node(y, "Make red overlay on input image"); arrow(top, y + 0.7); top = y; y -= 1.0
    node(y, "Persist input / mask / overlay PNGs"); arrow(top, y + 0.7); top = y; y -= 1.0
    node(y, "Return AnalysisResponse (JSON)"); arrow(top, y + 0.7); top = y; y -= 0.9
    node(y, "", kind="end"); arrow(top, y + 0.7)

    ax.text(3.75, 0.2, "Figure 5.2 — Activity Diagram: Analyze workflow",
            ha="center", fontsize=9, style="italic", color="#555")

    return _save(fig, "process_view_activity.png")


# =============================================================================
# PDF assembly (reportlab.platypus)
# =============================================================================

def _styles():
    ss = getSampleStyleSheet()
    base = ss["BodyText"]
    return {
        "Title": ParagraphStyle("Title", parent=ss["Title"], fontName="Helvetica-Bold",
                                fontSize=22, leading=26, alignment=TA_CENTER,
                                textColor=colors.HexColor("#1f4e79"), spaceAfter=10),
        "Subtitle": ParagraphStyle("Subtitle", parent=base, fontName="Helvetica",
                                   fontSize=14, leading=18, alignment=TA_CENTER,
                                   textColor=colors.HexColor("#333333"), spaceAfter=6),
        "CoverMeta": ParagraphStyle("CoverMeta", parent=base, fontName="Helvetica",
                                    fontSize=11, leading=14, alignment=TA_CENTER),
        "H1": ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                             fontSize=16, leading=20, spaceBefore=18, spaceAfter=10,
                             textColor=colors.HexColor("#1f4e79")),
        "H2": ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                             fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=6,
                             textColor=colors.HexColor("#2c5f8d")),
        "H3": ParagraphStyle("H3", parent=ss["Heading3"], fontName="Helvetica-Bold",
                             fontSize=11, leading=14, spaceBefore=8, spaceAfter=4,
                             textColor=colors.HexColor("#444444")),
        "Body": ParagraphStyle("Body", parent=base, fontName="Helvetica",
                               fontSize=10, leading=14, alignment=TA_JUSTIFY,
                               spaceAfter=6),
        "Bullet": ParagraphStyle("Bullet", parent=base, fontName="Helvetica",
                                 fontSize=10, leading=14, alignment=TA_LEFT,
                                 leftIndent=16, bulletIndent=4, spaceAfter=2),
        "Code": ParagraphStyle("Code", parent=base, fontName="Courier",
                               fontSize=8.2, leading=10.5, alignment=TA_LEFT,
                               textColor=colors.HexColor("#1a1a1a"),
                               backColor=colors.HexColor("#f4f6f9"),
                               borderColor=colors.HexColor("#d6dce6"),
                               borderWidth=0.5, borderPadding=6,
                               leftIndent=4, rightIndent=4, spaceAfter=10),
        "Caption": ParagraphStyle("Caption", parent=base, fontName="Helvetica-Oblique",
                                  fontSize=9, leading=12, alignment=TA_CENTER,
                                  textColor=colors.HexColor("#555555"), spaceAfter=8),
        "TableHeader": ParagraphStyle("TableHeader", parent=base, fontName="Helvetica-Bold",
                                      fontSize=9.5, leading=12, alignment=TA_LEFT,
                                      textColor=colors.white),
        "TableCell": ParagraphStyle("TableCell", parent=base, fontName="Helvetica",
                                    fontSize=9, leading=12, alignment=TA_LEFT),
    }


S = None  # populated in build()


def P(text, style="Body"):
    return Paragraph(text, S[style])


def B(text):
    return Paragraph(f"• {text}", S["Bullet"])


def code(text):
    # Escape minimal HTML for reportlab Paragraph and preserve newlines.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    text = text.replace("  ", "&nbsp;&nbsp;")
    return Paragraph(text, S["Code"])


def fig(path: Path, width_cm=16.5, caption=None):
    img = Image(str(path), width=width_cm * cm, height=width_cm * cm * 0.62)
    img._restrictSize(width_cm * cm, 22 * cm)
    out = [img]
    if caption:
        out.append(Paragraph(caption, S["Caption"]))
    return out


def make_table(rows, header=True, col_widths=None):
    data = []
    for i, row in enumerate(rows):
        if i == 0 and header:
            data.append([Paragraph(c, S["TableHeader"]) for c in row])
        else:
            data.append([Paragraph(c, S["TableCell"]) for c in row])
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#ffffff"), colors.HexColor("#f4f6f9")]),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#1f4e79")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfd8e3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
    t.setStyle(style)
    return t


# Code excerpts (kept short — full files in repo)
CODE_MAIN_PY = '''app = FastAPI(title="Nuclei MVP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**analysis_service.get_health())

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty upload.")
    try:
        result = analysis_service.analyze(payload, file.filename or "upload.png")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    return AnalysisResponse(**analysis_service.result_to_dict(result))

@app.get("/files/{filename}")
def get_file(filename: str):
    if "/" in filename or "\\\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    target = RESULT_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(target)'''

CODE_SCHEMAS = '''class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool
    mode: str = Field(description='"model" | "fallback-demo" | "uninitialised"')
    load_error: Optional[str] = None

class AnalysisMetadata(BaseModel):
    original_filename: str
    mode: str
    threshold: Optional[float] = None
    min_area: int
    image_size: int
    processing_ms: int
    device: str

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str
    cell_count: int
    input_url: str
    mask_url: str
    overlay_url: str
    metadata: AnalysisMetadata'''

CODE_SERVICE_ANALYZE = '''def analyze(image_bytes: bytes, original_filename: str) -> AnalysisResult:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Upload exceeds {MAX_UPLOAD_BYTES} bytes.")

    _ensure_model_loaded()

    job_id = uuid.uuid4().hex[:12]
    suffix = Path(original_filename).suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        suffix = ".png"

    upload_path = UPLOAD_DIR / f"{job_id}{suffix}"
    upload_path.write_bytes(image_bytes)

    image_rgb = _decode_image(image_bytes)

    started = time.perf_counter()
    if _mode == "model":
        mask = _predict_with_model(image_rgb)
        used_min_area = MIN_AREA
    else:
        mask = _predict_fallback(image_rgb)
        used_min_area = 20
    overlay = make_overlay(image_rgb, mask)
    cell_count = count_nuclei_from_binary(mask, min_area=used_min_area)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    cv2.imwrite(str(RESULT_DIR / f"{job_id}_input.png"),
                cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(RESULT_DIR / f"{job_id}_mask.png"), mask)
    cv2.imwrite(str(RESULT_DIR / f"{job_id}_overlay.png"),
                cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    return AnalysisResult(
        job_id=job_id,
        status="ok" if _mode == "model" else "ok-fallback",
        message=("Analysis complete (U-Net inference)." if _mode == "model"
                 else "Analysis complete (fallback demo mode)."),
        cell_count=int(cell_count),
        input_url=f"/files/{job_id}_input.png",
        mask_url=f"/files/{job_id}_mask.png",
        overlay_url=f"/files/{job_id}_overlay.png",
        metadata={
            "original_filename": original_filename,
            "mode": _mode,
            "threshold": THRESHOLD if _mode == "model" else None,
            "min_area": used_min_area,
            "image_size": IMAGE_SIZE,
            "processing_ms": elapsed_ms,
            "device": _device or "cpu",
        },
    )'''

CODE_LAZY_LOAD = '''def _ensure_model_loaded() -> None:
    """Load the U-Net checkpoint once. On failure, switch to fallback-demo."""
    global _model, _device, _mode, _load_error
    if _mode != "uninitialised":
        return
    try:
        import torch
        import segmentation_models_pytorch as smp
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        model = smp.Unet(
            encoder_name="resnet18",
            encoder_weights=None,
            in_channels=3,
            classes=1,
        ).to(_device)
        if not CHECKPOINT_PATH.exists():
            raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")
        state = torch.load(CHECKPOINT_PATH, map_location=_device)
        model.load_state_dict(state)
        model.eval()
        _model = model
        _mode = "model"
    except Exception as e:
        _load_error = f"{type(e).__name__}: {e}"
        _mode = "fallback-demo"
        _model = None'''

CODE_DB_JOB = '''class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class AnalysisJob(SQLModel, table=True):
    __tablename__ = "analysis_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default=JobStatus.pending.value, max_length=16, index=True)
    input_path: str = Field(max_length=500)
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )'''

CODE_UPLOAD_PANEL = '''export default function UploadPanel({
  file, previewUrl, busy, error, onFileSelected, onAnalyze,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFileSelected(f);
  }

  return (
    <div className="card">
      <h3>1 . Upload</h3>
      <div className={`upload-zone ${dragging ? "dragging" : ""}`}
           onDrop={handleDrop}
           onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
           onClick={() => inputRef.current?.click()}>
        <p>{file ? <strong>{file.name}</strong>
                 : "Drop a microscopy image, or click to browse."}</p>
        <input ref={inputRef} type="file" accept="image/*"
               style={{ display: "none" }} onChange={handleChange} />
      </div>
      {previewUrl && <img src={previewUrl} alt="preview" />}
      <button className="btn" disabled={!file || busy} onClick={onAnalyze}>
        {busy ? "Analysing..." : "Run analysis"}
      </button>
      {error && <div className="error">{error}</div>}
    </div>
  );
}'''

CODE_API_TS = '''export const API_BASE = "http://127.0.0.1:8080";

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
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}'''

CODE_RESULT_VIEWER = '''export default function ResultViewer({ result, busy }: Props) {
  if (!result) {
    return (
      <div className="card">
        <h3>2 . Result</h3>
        <p>{busy ? "Awaiting analysis output..."
                 : "Upload an image and click Run analysis."}</p>
      </div>
    );
  }
  const isModel = result.metadata.mode === "model";
  return (
    <div className="card">
      <h3>2 . Result . job {result.job_id}</h3>
      <div className="results-grid">
        <div className="result-tile"><h3>Original</h3>
          <img src={fileUrl(result.input_url)} alt="input" /></div>
        <div className="result-tile"><h3>Mask</h3>
          <img src={fileUrl(result.mask_url)} alt="mask" /></div>
        <div className="result-tile"><h3>Overlay</h3>
          <img src={fileUrl(result.overlay_url)} alt="overlay" /></div>
      </div>
      <MetricCard label="Estimated cell count" value={result.cell_count}
        caption={`${result.metadata.processing_ms} ms`} />
      <MetricCard label="Status" value={isModel ? "U-Net model" : "fallback demo"} />
    </div>
  );
}'''


# ---- Document body builder ---------------------------------------------------

def build_story():
    story = []

    # ---- Cover page
    story.append(Spacer(1, 4 * cm))
    story.append(P("Software Architecture Document", "Title"))
    story.append(P("Phase 1 &mdash; Version 1.0", "Subtitle"))
    story.append(Spacer(1, 0.6 * cm))
    story.append(P("Deeply Analytics", "Subtitle"))
    story.append(P("AI-Powered Microscopy Analysis &mdash; "
                   "Nuclei Segmentation and Cell Counting", "Subtitle"))
    story.append(Spacer(1, 1.8 * cm))

    cover_meta = [
        ["Course", "Software Architecture Project"],
        ["Phase", "Phase 1 &mdash; Architecture Design &amp; Initial Implementation"],
        ["Deadline", "04 May 2026"],
        ["Document version", "1.0"],
        ["Issue date", "02 May 2026"],
        ["Architectural style", "Layered REST API (FastAPI backend + React SPA)"],
        ["Modelling approach", "Kruchten 4+1 View Model (Use Case, Logical, Process)"],
        ["Repository", "github &mdash; project root (local)"],
    ]
    cover_table = make_table(cover_meta, header=False,
                             col_widths=[5 * cm, 11 * cm])
    cover_style = TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf2fb")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#ffffff"), colors.HexColor("#f4f6f9")]),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#1f4e79")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfd8e3")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
    ])
    cover_table.setStyle(cover_style)
    story.append(cover_table)
    story.append(PageBreak())

    # ---- Table of contents (manual)
    story.append(P("Table of Contents", "H1"))
    toc_items = [
        ("1. Introduction", ""),
        ("    1.1 Purpose of this document", ""),
        ("    1.2 Scope of Phase 1", ""),
        ("    1.3 The 4+1 view model", ""),
        ("    1.4 Definitions and acronyms", ""),
        ("2. System Selection (Step 1)", ""),
        ("    2.1 Target system: Deeply Analytics", ""),
        ("    2.2 Problem statement", ""),
        ("    2.3 System purpose and objectives", ""),
        ("    2.4 Target users", ""),
        ("    2.5 Core functionalities", ""),
        ("    2.6 Architectural style: layered REST API", ""),
        ("    2.7 Platform and technology stack", ""),
        ("3. Use Case View (Step 2.1)", ""),
        ("    3.1 Actors", ""),
        ("    3.2 Use case diagram", ""),
        ("    3.3 Use case specifications", ""),
        ("    3.4 Partial UI code", ""),
        ("4. Logical View (Step 2.2)", ""),
        ("    4.1 Logical decomposition", ""),
        ("    4.2 Class and component diagram", ""),
        ("    4.3 Component responsibilities", ""),
        ("    4.4 Key relationships", ""),
        ("    4.5 Partial backend code", ""),
        ("5. Process View (Step 2.3)", ""),
        ("    5.1 Runtime processes", ""),
        ("    5.2 Sequence diagram &mdash; analyze flow", ""),
        ("    5.3 Activity diagram &mdash; analyze flow", ""),
        ("    5.4 Health check flow", ""),
        ("    5.5 Concurrency, blocking, and fallback behaviour", ""),
        ("    5.6 Process-view code snippets", ""),
        ("6. Phase 1 Implementation Status", ""),
        ("7. References", ""),
        ("Appendix A &mdash; Repository layout", ""),
        ("Appendix B &mdash; Configuration reference", ""),
    ]
    for label, _ in toc_items:
        story.append(Paragraph(label, S["Body"]))
    story.append(PageBreak())

    # ---- 1. Introduction
    story.append(P("1. Introduction", "H1"))

    story.append(P("1.1 Purpose of this document", "H2"))
    story.append(P(
        "This document is the Software Architecture Document (SAD), "
        "version 1, for the <b>Deeply Analytics</b> system &mdash; an AI-powered "
        "web application for nuclei segmentation and cell counting in "
        "microscopy images. It is delivered as the Phase 1 milestone of the "
        "Software Architecture Project (deadline 04.05.2026). The document "
        "describes the target system, the architectural style chosen, and "
        "the first three views of the Kruchten 4+1 model: the Use Case "
        "view, the Logical view, and the Process view."))

    story.append(P("1.2 Scope of Phase 1", "H2"))
    story.append(P(
        "Phase 1 is a partial implementation: the system is functional "
        "end-to-end for a single user uploading and analysing one image at "
        "a time. The backend exposes three REST endpoints (health check, "
        "analyse, file download); the frontend is a single-page React + "
        "Vite + TypeScript application with a four-step workflow (Upload "
        "&rarr; Segment &rarr; Count &rarr; Report). Persistence, "
        "authentication, multi-project support, asynchronous job queues, "
        "and the Development and Physical views of the 4+1 model are out "
        "of scope for Phase 1 and will be addressed in Phase 2."))

    story.append(P("1.3 The 4+1 view model", "H2"))
    story.append(P(
        "Kruchten's 4+1 model decomposes a software architecture into five "
        "concurrent views, each chosen to communicate with a specific "
        "audience. Phase 1 covers three of them, plus a unifying scenario "
        "set (the Use Case view that ties everything together)."))
    story.append(B("<b>Use Case view</b> &mdash; functional scenarios from the "
                   "perspective of end users; ties the other views together."))
    story.append(B("<b>Logical view</b> &mdash; static decomposition of the "
                   "system into classes, modules, and components that satisfy "
                   "the functional requirements."))
    story.append(B("<b>Process view</b> &mdash; runtime behaviour, threads, "
                   "interactions between processes, and how concurrency and "
                   "blocking are handled."))
    story.append(B("<i>Development view</i> (Phase 2) &mdash; how source code "
                   "is organised into modules and packages."))
    story.append(B("<i>Physical view</i> (Phase 2) &mdash; how software maps "
                   "to deployment nodes (hosts, containers, networks)."))

    story.append(P("1.4 Definitions and acronyms", "H2"))
    defs = [
        ["Term", "Meaning"],
        ["SAD", "Software Architecture Document."],
        ["MVP", "Minimum Viable Product &mdash; smallest end-to-end version."],
        ["U-Net", "Convolutional encoder-decoder architecture used for biomedical "
                  "image segmentation (Ronneberger et al., 2015)."],
        ["MoNuSeg", "Multi-organ Nuclei Segmentation dataset; provides "
                    "histopathology images and XML nucleus annotations."],
        ["CC labelling", "Connected-component labelling &mdash; an OpenCV "
                         "operation that groups adjacent foreground pixels "
                         "into discrete objects, used here to count nuclei."],
        ["JWT", "JSON Web Token &mdash; planned auth mechanism (Phase 2)."],
        ["ORM", "Object-Relational Mapper &mdash; SQLModel/SQLAlchemy."],
        ["SPA", "Single-Page Application &mdash; the React frontend."],
        ["DTO", "Data Transfer Object &mdash; here, Pydantic schemas."],
    ]
    story.append(make_table(defs, col_widths=[3.5 * cm, 12.5 * cm]))

    story.append(PageBreak())

    # ---- 2. System Selection
    story.append(P("2. System Selection (Step 1)", "H1"))

    story.append(P("2.1 Target system: Deeply Analytics", "H2"))
    story.append(P(
        "<b>Deeply Analytics</b> is a web-based platform that lets a "
        "biomedical researcher upload a microscopy image and receive, in "
        "seconds, a segmentation mask of the cell nuclei it contains, an "
        "overlay visualisation, and a cell-count estimate. The system is "
        "built on top of a trained U-Net (ResNet-18 encoder, "
        "<i>segmentation_models_pytorch</i>) and a connected-component "
        "post-processor that converts the binary mask into discrete nuclei "
        "objects."))

    story.append(P("2.2 Problem statement", "H2"))
    story.append(P(
        "Manual nuclei counting on histopathology slides is slow "
        "(several minutes per field of view), inconsistent between "
        "observers, and does not scale to studies that produce thousands "
        "of images. Existing offline scripts solve the throughput problem "
        "but require a Python environment, a GPU, and command-line "
        "literacy &mdash; none of which are typical for a wet-lab "
        "researcher. Deeply Analytics replaces the manual step with a "
        "browser-based workflow that anyone in the lab can use."))

    story.append(P("2.3 System purpose and objectives", "H2"))
    story.append(B("Reduce time spent on manual nuclei counting from minutes "
                   "to seconds per image."))
    story.append(B("Produce repeatable, operator-independent counts."))
    story.append(B("Expose the AI pipeline through a usable REST API and "
                   "single-page web interface."))
    story.append(B("Provide a clean architectural baseline that can grow "
                   "into a multi-user SaaS in Phase 2 without rewrites."))
    story.append(B("Demonstrate sound application of the 4+1 architectural "
                   "model and a layered REST architecture."))

    story.append(P("2.4 Target users", "H2"))
    users = [
        ["Actor", "Role / context", "Primary goals"],
        ["Researcher",
         "Biomedical or histopathology researcher analysing nuclei in tissue sections.",
         "Upload an image, get a count and a mask, download the overlay for a paper."],
        ["Lab Technician",
         "Wet-lab staff running routine cell counts.",
         "Upload an image, view the result, repeat the workflow on a batch of slides."],
        ["Admin / Monitoring",
         "Developer or operations role; in Phase 2, system administrator.",
         "Check that the backend and the U-Net model are healthy via /api/health."],
    ]
    story.append(make_table(users, col_widths=[3 * cm, 6.5 * cm, 6.5 * cm]))

    story.append(P("2.5 Core functionalities", "H2"))
    funcs = [
        ["ID", "Functionality", "Description", "Status"],
        ["F-1", "Upload microscopy image",
         "Accept PNG/JPG/TIFF up to 25 MB via multipart/form-data.",
         "Implemented"],
        ["F-2", "Run nuclei segmentation",
         "Run the U-Net model on the resized 256x256 image, applying sigmoid > 0.8 threshold.",
         "Implemented"],
        ["F-3", "Count nuclei",
         "Apply connected-component labelling on the binary mask to estimate cell count.",
         "Implemented"],
        ["F-4", "Generate overlay visualisation",
         "Composite the predicted mask onto the input as a red-tinted overlay.",
         "Implemented"],
        ["F-5", "Persist artefacts",
         "Save the input, the mask, and the overlay as PNGs in the storage layer.",
         "Implemented (local FS)"],
        ["F-6", "Download artefacts",
         "Serve PNG artefacts via GET /files/{filename} with path-traversal protection.",
         "Implemented"],
        ["F-7", "Health monitoring",
         "Report device, model load status, and operating mode via GET /api/health.",
         "Implemented"],
        ["F-8", "Fallback demo path",
         "If the U-Net checkpoint cannot load, switch to an Otsu-threshold demo so the "
         "UI is testable end-to-end.",
         "Implemented"],
        ["F-9", "Multi-user persistence",
         "Persist users, projects, jobs, and results in PostgreSQL.",
         "Proposed (Phase 2)"],
        ["F-10", "Authentication",
         "JWT-based login with role-based access control.",
         "Proposed (Phase 2)"],
        ["F-11", "Asynchronous jobs",
         "Run inference on a background worker so the API never blocks.",
         "Proposed (Phase 2)"],
    ]
    story.append(make_table(funcs, col_widths=[1.2 * cm, 3.8 * cm, 8.5 * cm, 2.7 * cm]))

    story.append(P("2.6 Architectural style: layered REST API", "H2"))
    story.append(P(
        "The system follows a <b>layered architecture</b> with a "
        "<b>REST API</b> as the integration boundary. Each layer has a "
        "single concern and depends only on the layer below it."))
    layers = [
        ["Layer", "Responsibility", "Implementation"],
        ["Presentation (frontend)",
         "Render UI, capture file uploads, display results.",
         "React 18 + Vite + TypeScript SPA."],
        ["API (route layer)",
         "HTTP transport, validation, error mapping.",
         "FastAPI routers + Pydantic schemas (backend/main.py)."],
        ["Service (orchestration)",
         "Coordinate analysis workflow: load model, decode, predict, count, persist.",
         "backend/services/analysis_service.py."],
        ["AI processing",
         "Pure inference and image post-processing.",
         "PyTorch U-Net + OpenCV + NumPy (src/infer.py, src/batch_count_refined.py)."],
        ["Data / storage",
         "Persist artefacts and (in Phase 2) structured records.",
         "Local filesystem today; PostgreSQL + SQLModel proposed."],
    ]
    story.append(make_table(layers, col_widths=[4 * cm, 6.5 * cm, 5.5 * cm]))

    story.append(P("2.7 Platform and technology stack", "H2"))
    stack = [
        ["Layer", "Technology", "Version", "Status"],
        ["Frontend framework", "React + React DOM", "18.3.1", "Implemented"],
        ["Frontend tooling", "Vite + TypeScript", "5.4 / 5.5", "Implemented"],
        ["Backend framework", "FastAPI", "0.104.x", "Implemented"],
        ["ASGI server", "Uvicorn", "0.46.0", "Implemented"],
        ["Validation", "Pydantic + pydantic-settings", "2.12", "Implemented"],
        ["AI framework", "PyTorch", "2.10", "Implemented"],
        ["Segmentation models", "segmentation_models_pytorch", "0.5.0", "Implemented"],
        ["Image processing", "OpenCV, NumPy, scikit-image", "4.13 / 2.4 / 0.26", "Implemented"],
        ["Storage", "Local filesystem (storage_root)", "&mdash;", "Implemented"],
        ["Persistence (target)", "PostgreSQL + SQLModel + Alembic", "16 / 0.0.14 / 0.24", "Proposed"],
        ["Authentication (target)", "JWT (HS256)", "&mdash;", "Proposed"],
        ["Async jobs (target)", "FastAPI BackgroundTasks &rarr; Celery + Redis", "&mdash;", "Proposed"],
    ]
    story.append(make_table(stack, col_widths=[4.2 * cm, 6 * cm, 3.3 * cm, 2.5 * cm]))

    story.append(PageBreak())

    # ---- 3. Use Case View
    story.append(P("3. Use Case View (Step 2.1)", "H1"))
    story.append(P(
        "The Use Case view captures the system from the perspective of "
        "the actors that interact with it. It defines what the system "
        "must do, leaving how it does it to the Logical and Process "
        "views."))

    story.append(P("3.1 Actors", "H2"))
    story.append(B("<b>Researcher</b> &mdash; primary user. Uploads "
                   "microscopy images, runs analyses, views results, "
                   "downloads artefacts."))
    story.append(B("<b>Lab Technician</b> &mdash; routine user. Uploads "
                   "images and reads the cell count without going deep "
                   "into the data."))
    story.append(B("<b>Admin / Monitoring</b> &mdash; technical operator. "
                   "Calls the health endpoint to check that the backend "
                   "and the model are alive. In Phase 2 this actor will "
                   "also manage users and projects."))

    story.append(P("3.2 Use case diagram", "H2"))
    story.extend(fig(DIAGRAMS_DIR / "use_case_diagram.png", width_cm=16.0,
                     caption="Figure 3.1 &mdash; Use Case Diagram"))

    story.append(P("3.3 Use case specifications", "H2"))

    use_cases = [
        {
            "id": "UC-1 &mdash; Upload microscopy image",
            "actor": "Researcher, Lab Technician",
            "pre": "The user has the application open in a browser; the "
                   "backend is reachable; the file is a supported image "
                   "type (PNG, JPG, TIFF) and is under 25 MB.",
            "main": [
                "The user drags an image onto the upload zone, or clicks to browse.",
                "The frontend validates the file type and reads it into a File object.",
                "The frontend renders a local preview of the image.",
                "The Run-analysis button becomes enabled.",
            ],
            "alt": "If the user selects a non-image file, the browser file dialog filters "
                   "it out; if a corrupt image is dropped, UC-2 will reject it with HTTP 400.",
            "post": "A File reference is held in component state, ready for UC-2.",
        },
        {
            "id": "UC-2 &mdash; Run nuclei analysis",
            "actor": "Researcher, Lab Technician",
            "pre": "UC-1 has completed; the backend is reachable.",
            "main": [
                "The user clicks Run analysis.",
                "The frontend POSTs the file as multipart/form-data to /api/analyze.",
                "The FastAPI router validates the MIME type and the size.",
                "The AnalysisService lazy-loads the U-Net checkpoint on first call.",
                "The service decodes and resizes the image to 256x256.",
                "The U-Net produces logits, sigmoid is applied, threshold 0.8 yields a binary mask.",
                "make_overlay() composites the mask onto the input as a red overlay.",
                "count_nuclei_from_binary() counts connected components.",
                "The service writes input, mask, and overlay PNGs to storage.",
                "The router returns AnalysisResponse JSON containing job_id, cell_count, and three URLs.",
            ],
            "alt": "If the U-Net checkpoint is missing or fails to load, the service runs "
                   "an Otsu-threshold fallback path and returns status 'ok-fallback'. If the "
                   "uploaded file is not an image or is empty, the router returns HTTP 400. "
                   "If any other error occurs, HTTP 500 with the exception message is returned.",
            "post": "Three artefacts (input, mask, overlay) exist on disk; the response JSON "
                    "contains the cell count and the URLs needed by UC-3 and UC-4.",
        },
        {
            "id": "UC-3 &mdash; View analysis result",
            "actor": "Researcher, Lab Technician",
            "pre": "UC-2 has returned a successful AnalysisResponse.",
            "main": [
                "The frontend transitions the workflow stage from 'count' to 'report'.",
                "ResultViewer renders a three-tile grid: Original, Mask, Overlay.",
                "The cell count and the processing time are shown as metric cards.",
                "A status badge indicates whether the U-Net or the fallback path produced the result.",
            ],
            "alt": "If the response is missing (network failure mid-call), the UI returns to "
                   "the upload stage and displays a red error message.",
            "post": "The user can read the count, see the segmentation, and decide whether to download.",
        },
        {
            "id": "UC-4 &mdash; Download artefacts",
            "actor": "Researcher",
            "pre": "UC-3 has rendered the results; the user wants to save the mask or the overlay.",
            "main": [
                "The user right-clicks the mask or overlay tile and chooses Save image as.",
                "The browser issues GET /files/{filename} to the backend.",
                "The router rejects any filename containing '/', '\\\\', or '..' (path-traversal guard).",
                "If the file exists in the result directory, FastAPI returns it via FileResponse.",
            ],
            "alt": "If the filename is invalid, the backend returns HTTP 400. If the file does "
                   "not exist, HTTP 404.",
            "post": "The PNG is saved to the user's local filesystem.",
        },
        {
            "id": "UC-5 &mdash; Check system health",
            "actor": "Admin / Monitoring",
            "pre": "The backend process is running.",
            "main": [
                "The actor (or the React app on mount) issues GET /api/health.",
                "The router calls AnalysisService.get_health(), which lazy-loads the model on first call.",
                "The response contains: status, device (cpu/cuda), model_loaded, mode, load_error.",
            ],
            "alt": "If the U-Net checkpoint is missing, mode = 'fallback-demo' and load_error "
                   "carries the original exception text. The endpoint still returns HTTP 200 because "
                   "the API itself is healthy &mdash; only the AI subsystem is degraded.",
            "post": "The actor knows whether the backend, the device, and the model are operational.",
        },
    ]

    for uc in use_cases:
        story.append(P(uc["id"], "H3"))
        story.append(make_table([
            ["Field", "Value"],
            ["Actor(s)", uc["actor"]],
            ["Precondition", uc["pre"]],
            ["Postcondition", uc["post"]],
            ["Alternative flow", uc["alt"]],
        ], col_widths=[3.2 * cm, 12.8 * cm]))
        story.append(Spacer(1, 4))
        story.append(P("<b>Main flow</b>", "Body"))
        for i, step in enumerate(uc["main"], 1):
            story.append(P(f"{i}. {step}", "Bullet"))
        story.append(Spacer(1, 6))

    story.append(P("3.4 Partial UI code", "H2"))
    story.append(P("The following excerpts show the UI surface that "
                   "supports UC-1 through UC-3. Full source: "
                   "<i>frontend/src/components/UploadPanel.tsx</i>, "
                   "<i>ResultViewer.tsx</i>, and <i>api.ts</i>.", "Body"))
    story.append(P("UploadPanel.tsx (drag-drop + run analysis)", "H3"))
    story.append(code(CODE_UPLOAD_PANEL))
    story.append(P("api.ts (fetch wrapper)", "H3"))
    story.append(code(CODE_API_TS))
    story.append(P("ResultViewer.tsx (results grid)", "H3"))
    story.append(code(CODE_RESULT_VIEWER))

    story.append(PageBreak())

    # ---- 4. Logical View
    story.append(P("4. Logical View (Step 2.2)", "H1"))
    story.append(P(
        "The Logical view describes the static decomposition of the "
        "system into modules and the relationships between them. It "
        "answers <i>what</i> the code is, not <i>when</i> it runs."))

    story.append(P("4.1 Logical decomposition", "H2"))
    story.append(P(
        "Deeply Analytics is divided into six logical components, plus a "
        "proposed persistence cluster (User, Project, AnalysisJob, "
        "AnalysisResult) that is designed but not yet wired:"))
    story.append(B("<b>React UI</b> &mdash; the SPA the user sees in the "
                   "browser. Three components carry the workflow: "
                   "UploadPanel, ResultViewer, and WorkflowSteps. A thin "
                   "<i>api.ts</i> wraps fetch."))
    story.append(B("<b>FastAPI App</b> &mdash; the HTTP boundary. Three "
                   "routes (health, analyze, files) and CORS middleware."))
    story.append(B("<b>Pydantic Schemas</b> &mdash; declarative DTOs that "
                   "validate every request and response and generate OpenAPI."))
    story.append(B("<b>AnalysisService</b> &mdash; the orchestrator. Owns "
                   "the model singleton, decodes images, calls the U-Net or "
                   "the fallback, runs counting, persists artefacts."))
    story.append(B("<b>U-Net model</b> &mdash; the PyTorch network "
                   "(<i>smp.Unet</i> with ResNet-18 encoder), loaded once "
                   "and held as a module-level singleton."))
    story.append(B("<b>OpenCV postprocessor</b> &mdash; image decode, "
                   "resize, overlay rendering (<i>src.infer.make_overlay</i>) "
                   "and connected-component counting "
                   "(<i>src.batch_count_refined.count_nuclei_from_binary</i>)."))
    story.append(B("<b>Storage</b> &mdash; the filesystem under "
                   "<i>backend/storage/</i> with <i>uploads/</i> and "
                   "<i>results/</i> subfolders."))
    story.append(B("<b>Persistence (proposed)</b> &mdash; SQLModel tables "
                   "User, Project, AnalysisJob, AnalysisResult; the schema "
                   "exists in <i>backend/db/models/</i> but no router uses "
                   "it yet."))

    story.append(P("4.2 Class and component diagram", "H2"))
    story.extend(fig(DIAGRAMS_DIR / "logical_view_class_diagram.png", width_cm=17.0,
                     caption="Figure 4.1 &mdash; Logical View: components and relationships"))

    story.append(P("4.3 Component responsibilities", "H2"))
    resp = [
        ["Component", "Source file(s)", "Responsibility"],
        ["React UI",
         "frontend/src/App.tsx, components/*.tsx",
         "Owns workflow stage, renders panels, calls /api/health on mount, "
         "issues /api/analyze on user click."],
        ["api.ts",
         "frontend/src/api.ts",
         "Single source of truth for the API base URL and request shapes; "
         "wraps fetch and parses JSON."],
        ["FastAPI App",
         "backend/main.py",
         "Defines the three HTTP routes; applies CORS; maps service errors "
         "to HTTP 400 / 500."],
        ["Pydantic Schemas",
         "backend/schemas.py",
         "Defines HealthResponse, AnalysisMetadata, AnalysisResponse; "
         "ensures the contract with the frontend stays explicit."],
        ["AnalysisService",
         "backend/services/analysis_service.py",
         "Core workflow: lazy-load checkpoint, decode image, predict, count, "
         "persist, return AnalysisResult dataclass."],
        ["Settings",
         "backend/config.py",
         "Pydantic BaseSettings; reads env vars and .env; exposes derived "
         "paths (upload_dir, result_dir, checkpoint_path)."],
        ["U-Net model",
         "(loaded from outputs/checkpoints/best_model.pth)",
         "ResNet-18 encoder + U-Net decoder, 1 output channel; produces "
         "logits that are sigmoid-thresholded at 0.8."],
        ["OpenCV postprocessor",
         "src/infer.py, src/batch_count_refined.py",
         "make_overlay() and count_nuclei_from_binary() are reused "
         "verbatim from the offline pipeline."],
        ["Storage",
         "backend/storage/{uploads,results}",
         "Holds the original upload (one per job) and three PNGs per "
         "completed analysis."],
        ["Persistence (proposed)",
         "backend/db/models/*.py",
         "SQLModel tables with foreign-key relationships; not yet exposed "
         "by any router."],
    ]
    story.append(make_table(resp, col_widths=[3.2 * cm, 4.6 * cm, 8.2 * cm]))

    story.append(P("4.4 Key relationships", "H2"))
    story.append(B("<b>Composition</b>: AnalysisService composes the U-Net "
                   "model and the OpenCV postprocessor; their lifecycles "
                   "are tied to the service module."))
    story.append(B("<b>Dependency</b>: FastAPI routes depend on "
                   "AnalysisService and on Pydantic schemas; the schemas "
                   "depend on no internal module."))
    story.append(B("<b>Uses</b>: AnalysisService uses Settings to discover "
                   "paths and thresholds; it never reads environment "
                   "variables directly."))
    story.append(B("<b>Foreign keys (proposed)</b>: AnalysisJob references "
                   "User and Project; AnalysisResult references AnalysisJob "
                   "with a unique constraint (one result per job)."))
    story.append(B("<b>HTTPS boundary</b>: the React UI talks to the FastAPI "
                   "app over JSON; in Phase 2 a JWT will travel in an "
                   "<i>HttpOnly</i> cookie."))

    story.append(P("4.5 Partial backend code", "H2"))
    story.append(P("backend/main.py &mdash; FastAPI routes", "H3"))
    story.append(code(CODE_MAIN_PY))
    story.append(P("backend/schemas.py &mdash; Pydantic DTOs", "H3"))
    story.append(code(CODE_SCHEMAS))
    story.append(P("backend/db/models/analysis_job.py &mdash; proposed persistence", "H3"))
    story.append(code(CODE_DB_JOB))

    story.append(PageBreak())

    # ---- 5. Process View
    story.append(P("5. Process View (Step 2.3)", "H1"))
    story.append(P(
        "The Process view explains how the system behaves at runtime: "
        "which processes exist, how they communicate, where they block, "
        "and how concurrency is handled."))

    story.append(P("5.1 Runtime processes", "H2"))
    story.append(P(
        "In Phase 1 the backend runs as a single Uvicorn worker process. "
        "Inside that process, FastAPI dispatches HTTP requests to async "
        "handlers; the analysis handler is declared <i>async</i> but "
        "delegates to a synchronous service (the U-Net forward pass is "
        "synchronous PyTorch). The U-Net is loaded once on first use and "
        "kept as a module-level singleton inside <i>analysis_service.py</i>; "
        "subsequent requests reuse the loaded model. The frontend runs in "
        "the user's browser as a React SPA served by the Vite dev server "
        "in development; in Phase 2 it is built to static assets and "
        "served by a CDN. No background workers, queues, or long-running "
        "tasks exist in Phase 1."))

    story.append(P("5.2 Sequence diagram &mdash; analyze flow", "H2"))
    story.extend(fig(DIAGRAMS_DIR / "process_view_sequence.png", width_cm=17.0,
                     caption="Figure 5.1 &mdash; Sequence Diagram: POST /api/analyze"))

    story.append(P("5.3 Activity diagram &mdash; analyze flow", "H2"))
    story.extend(fig(DIAGRAMS_DIR / "process_view_activity.png", width_cm=11.0,
                     caption="Figure 5.2 &mdash; Activity Diagram: analyze workflow"))

    story.append(P("5.4 Health check flow", "H2"))
    story.append(P(
        "GET /api/health is a short-circuit synchronous flow: the route "
        "calls <i>analysis_service.get_health()</i>, which calls "
        "<i>_ensure_model_loaded()</i> (no-op after the first call) and "
        "returns a dict with the device, the model_loaded boolean, the "
        "operating mode, and any load error. The React app calls this "
        "endpoint on mount so that the header badge can show "
        "<i>backend: model &middot; cpu</i> or <i>backend: fallback-demo</i> "
        "before the user even attempts to analyse an image."))

    story.append(P("5.5 Concurrency, blocking, and fallback behaviour", "H2"))
    story.append(B("<b>Single-process MVP.</b> Multiple concurrent requests "
                   "are accepted but the U-Net forward pass holds the "
                   "Python GIL, so two simultaneous analyses are serialised "
                   "in practice. This is acceptable for a single-user MVP; "
                   "in Phase 2 a Celery + Redis worker pool will run "
                   "inference jobs in parallel processes."))
    story.append(B("<b>Lazy initialisation.</b> The U-Net is loaded on the "
                   "first request that needs it. The first request after a "
                   "cold start therefore takes a few seconds longer than "
                   "subsequent requests; this is documented in the health "
                   "endpoint by the transition <i>uninitialised &rarr; "
                   "model</i>."))
    story.append(B("<b>Graceful fallback.</b> If the checkpoint file is "
                   "missing, corrupted, or incompatible with the current "
                   "<i>segmentation_models_pytorch</i> version, "
                   "<i>_ensure_model_loaded()</i> catches the exception, "
                   "stores it in <i>_load_error</i>, and switches the "
                   "service into <i>fallback-demo</i> mode (Otsu threshold "
                   "+ morphological opening). The API contract is "
                   "preserved; only the response status changes from "
                   "<i>ok</i> to <i>ok-fallback</i>."))
    story.append(B("<b>Bounded inputs.</b> The request body is rejected "
                   "before it is touched if the content type is not "
                   "<i>image/*</i>, if the upload is empty, or if it "
                   "exceeds <i>max_upload_bytes</i> (25 MB). This bounds "
                   "the per-request memory footprint."))
    story.append(B("<b>Path-traversal protection.</b> GET /files/"
                   "{filename} rejects any name containing <i>/</i>, "
                   "<i>\\\\</i>, or <i>..</i> before resolving the path. "
                   "This prevents the file-download route from leaking "
                   "files outside the result directory."))

    story.append(P("5.6 Process-view code snippets", "H2"))
    story.append(P("AnalysisService.analyze() &mdash; orchestration body", "H3"))
    story.append(code(CODE_SERVICE_ANALYZE))
    story.append(P("_ensure_model_loaded() &mdash; lazy init pattern", "H3"))
    story.append(code(CODE_LAZY_LOAD))

    story.append(PageBreak())

    # ---- 6. Implementation status
    story.append(P("6. Phase 1 Implementation Status", "H1"))
    story.append(P(
        "This section records what was actually built for the Phase 1 "
        "milestone, separately from what is designed and documented in "
        "Sections 3 to 5. It is intended to be honest about which parts "
        "of the architecture are running today and which are planned."))

    story.append(P("6.1 What is implemented", "H2"))
    story.append(B("FastAPI backend with three working routes: "
                   "<i>/api/health</i>, <i>/api/analyze</i>, "
                   "<i>/files/{filename}</i>."))
    story.append(B("PyTorch U-Net inference (ResNet-18 encoder), with a "
                   "trained checkpoint at <i>outputs/checkpoints/best_model.pth</i>."))
    story.append(B("OpenCV-based connected-component nuclei counter and "
                   "red-tinted overlay generator, reused from the offline "
                   "pipeline in <i>src/</i>."))
    story.append(B("Otsu-threshold fallback path that keeps the API "
                   "contract usable when the checkpoint cannot be loaded."))
    story.append(B("React 18 + Vite + TypeScript single-page app with "
                   "drag-drop upload, four-step workflow indicator, and "
                   "result tile grid (Original / Mask / Overlay)."))
    story.append(B("Local filesystem storage layout with deterministic "
                   "filenames keyed by a 12-character job_id."))
    story.append(B("Pydantic settings loaded from <i>.env</i> with safe "
                   "defaults so the app boots without any environment "
                   "configuration."))

    story.append(P("6.2 What is proposed for Phase 2", "H2"))
    story.append(B("PostgreSQL persistence: User, Project, AnalysisJob, "
                   "AnalysisResult tables (the SQLModel schema is already "
                   "drafted in <i>backend/db/models/</i>)."))
    story.append(B("Authentication and authorisation: JWT issuance, login "
                   "and refresh routes, role-based access control, and "
                   "ownership checks on every project-scoped resource."))
    story.append(B("Asynchronous job processing: dispatch the analyse "
                   "step to a Celery + Redis worker pool so the HTTP "
                   "request returns immediately with a job ID and the "
                   "frontend polls for status."))
    story.append(B("Multi-page dashboard: login, project list, history, "
                   "morphology features, density heatmaps, and exports."))
    story.append(B("S3-compatible object storage replacing the local "
                   "<i>storage/</i> tree for production deployments."))
    story.append(B("Development view and Physical view added to the SAD "
                   "(version 2)."))

    story.append(P("6.3 Verified end-to-end", "H2"))
    story.append(P(
        "Twelve sample analyses are present in "
        "<i>backend/storage/results/</i>, each producing the expected "
        "trio of <i>{job_id}_input.png</i>, <i>{job_id}_mask.png</i>, "
        "and <i>{job_id}_overlay.png</i>. They demonstrate that the "
        "analyse flow described in Sections 5.2 and 5.3 runs to "
        "completion against real microscopy inputs and that the storage "
        "naming convention from Section 4 is honoured."))

    story.append(PageBreak())

    # ---- 7. References
    story.append(P("7. References", "H1"))
    refs = [
        "Kruchten, P. (1995). <i>The 4+1 View Model of Architecture</i>. IEEE Software, 12(6), 42-50.",
        "Ronneberger, O., Fischer, P., &amp; Brox, T. (2015). "
        "<i>U-Net: Convolutional Networks for Biomedical Image Segmentation</i>. MICCAI, 234-241.",
        "Iakubovskii, P. (2019). <i>Segmentation Models PyTorch</i>. "
        "GitHub: qubvel/segmentation_models.pytorch.",
        "Paszke, A. et al. (2019). <i>PyTorch: An Imperative Style, "
        "High-Performance Deep Learning Library</i>. NeurIPS 32.",
        "Bradski, G. (2000). <i>The OpenCV Library</i>. Dr. Dobb's Journal of Software Tools.",
        "Tiangolo, S. (2018-). <i>FastAPI Documentation</i>. https://fastapi.tiangolo.com/",
        "Colvin, S. (2017-). <i>Pydantic Documentation</i>. https://docs.pydantic.dev/",
        "Tiangolo, S. (2021-). <i>SQLModel Documentation</i>. https://sqlmodel.tiangolo.com/",
        "Bayer, M. (2010-). <i>Alembic Documentation</i>. https://alembic.sqlalchemy.org/",
    ]
    for r in refs:
        story.append(P("&bull; " + r, "Body"))

    story.append(PageBreak())

    # ---- Appendix A
    story.append(P("Appendix A &mdash; Repository layout", "H1"))
    repo_tree = """project/
+-- backend/
|   +-- main.py                FastAPI app, 3 routes
|   +-- config.py              Pydantic Settings
|   +-- schemas.py             Pydantic response models
|   +-- services/
|   |   \\-- analysis_service.py    Orchestration + U-Net wrapper
|   +-- db/
|   |   +-- base.py            SQLModel metadata
|   |   +-- session.py         Lazy engine + get_session()
|   |   \\-- models/
|   |       +-- user.py
|   |       +-- project.py
|   |       +-- analysis_job.py
|   |       \\-- analysis_result.py
|   +-- alembic/               Migration scripts
|   \\-- storage/
|       +-- uploads/           One file per upload
|       \\-- results/           {job}_input.png / _mask.png / _overlay.png
+-- frontend/
|   +-- index.html
|   +-- package.json           React 18, Vite 5, TypeScript
|   +-- vite.config.ts
|   \\-- src/
|       +-- main.tsx           React 18 root
|       +-- App.tsx            Workflow orchestrator
|       +-- api.ts             fetch wrapper + DTOs
|       +-- styles.css         Design tokens
|       \\-- components/
|           +-- UploadPanel.tsx
|           +-- ResultViewer.tsx
|           +-- WorkflowSteps.tsx
|           \\-- MetricCard.tsx
+-- src/                       Offline AI pipeline (training, batch inference)
|   +-- train.py
|   +-- infer.py               make_overlay()
|   +-- batch_count_refined.py  count_nuclei_from_binary()
|   +-- ... (dataset, metrics, postprocess, density, morphology)
+-- data/
|   +-- raw/
|   +-- processed/
|   \\-- splits/                train.csv / val.csv / test.csv / all.csv
+-- outputs/
|   +-- checkpoints/best_model.pth     Trained U-Net
|   +-- counting_batch_refined_xmlgt/  Batch inference outputs
|   +-- density_maps/
|   \\-- morphology/
+-- docs/                      Architecture and design documents
+-- scripts/
|   \\-- build_sad_phase1.py    Builds this PDF
+-- requirements.txt
+-- .env.example
\\-- README.md
"""
    story.append(code(repo_tree))

    story.append(P("Appendix B &mdash; Configuration reference", "H1"))
    story.append(P("All settings are loaded by <i>backend/config.py</i> "
                   "via <i>pydantic-settings</i>. Defaults are safe so "
                   "the app boots without an .env file.", "Body"))
    cfg = [
        ["Setting", "Default", "Purpose"],
        ["env", "dev", "Environment selector (dev / staging / prod)."],
        ["allowed_origins", "[localhost:5173, 127.0.0.1:5173]", "CORS allow-list (Vite dev server)."],
        ["database_url", "(unset)", "Phase 2: PostgreSQL DSN."],
        ["jwt_secret", "(unset)", "Phase 2: HS256 signing key."],
        ["jwt_alg", "HS256", "Phase 2: JWT algorithm."],
        ["jwt_ttl_seconds", "3600", "Phase 2: token lifetime."],
        ["storage_root", "{ROOT}/backend/storage", "Filesystem root for uploads and results."],
        ["model_checkpoint", "outputs/checkpoints/best_model.pth", "Path to the trained U-Net weights."],
        ["image_size", "256", "Fixed input/output resolution; tied to the trained network."],
        ["threshold", "0.8", "Sigmoid threshold for the binary mask."],
        ["min_area", "1", "Minimum connected-component size to count (model path)."],
        ["max_upload_bytes", "26214400 (25 MB)", "Hard cap on a single upload."],
        ["rate_limit_*", "10 / 30 / 60 / minute", "Phase 2: per-route rate limits."],
    ]
    story.append(make_table(cfg, col_widths=[4 * cm, 4.5 * cm, 7.5 * cm]))

    return story


def build():
    global S
    S = _styles()

    # 1. Render diagrams
    print("Rendering use_case_diagram.png ...")
    draw_use_case_diagram()
    print("Rendering logical_view_class_diagram.png ...")
    draw_logical_view_class_diagram()
    print("Rendering process_view_sequence.png ...")
    draw_sequence_diagram()
    print("Rendering process_view_activity.png ...")
    draw_activity_diagram()

    # 2. Build PDF
    print(f"Assembling PDF -> {PDF_OUT}")
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
        title="Software Architecture Document - Phase 1 v1 - Deeply Analytics",
        author="Deeply Analytics Team",
    )

    story = build_story()

    def _on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(2.0 * cm, 1.2 * cm,
                          "Deeply Analytics — SAD v1 — Phase 1")
        canvas.drawRightString(A4[0] - 2.0 * cm, 1.2 * cm,
                               f"Page {doc_.page}")
        canvas.setStrokeColor(colors.HexColor("#cccccc"))
        canvas.line(2.0 * cm, 1.5 * cm, A4[0] - 2.0 * cm, 1.5 * cm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)

    size_kb = PDF_OUT.stat().st_size / 1024
    print(f"Wrote {PDF_OUT} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    build()
