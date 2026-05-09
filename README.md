<div align="center">

# Nuclei AI

### AI-Based Cell Nuclei Segmentation, Counting & Morphology
### for Histopathology Microscopy

**A polished, end-to-end U-Net pipeline behind a FastAPI service and a React dashboard.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg?logo=react)](https://react.dev)
[![PyTorch 2.x](https://img.shields.io/badge/PyTorch-2.x-ee4c2c.svg?logo=pytorch)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests: 20 passing](https://img.shields.io/badge/tests-20%20passing-success.svg)](tests/)
[![Status: MVP](https://img.shields.io/badge/status-MVP%20v0.3-brightgreen.svg)](CHANGELOG.md)

</div>

---

## What it does

Nuclei AI takes a hematoxylin-and-eosin (H&E) microscopy tile, runs it through a U-Net
(ResNet18 encoder) trained on the **MoNuSeg** dataset, and returns:

- a binary segmentation mask of every nucleus,
- a translucent overlay for visual review,
- a connected-components count (`τ = 0.7`, `min_area = 5`),
- per-image morphology features (area, perimeter, circularity, eccentricity),
- a density heatmap that highlights cluster hot-spots.

The same trained model is exposed three ways:

1. **Production UI** — React 18 + Vite + Tailwind, with persistent history, dark/light theme, mobile-responsive layout, demo mode, and error boundaries.
2. **REST API** — FastAPI 0.136 with structured JSON logs, rate limiting, ETag caching, and SQLite/Postgres persistence.
3. **Research dashboard** — Streamlit ([src/app.py](src/app.py)) for inspecting pre-computed pipeline outputs (counts, masks, density, morphology).

---

## Architecture

```text
┌──────────────────────────┐                ┌────────────────────────────────┐
│   React 18 + Vite + TS   │                │           FastAPI              │
│  (Dashboard / Workflow)  │ ◄── HTTP ────► │    /api/health                 │
│                          │                │    /api/analyze                │
│  • Demo mode             │                │    /api/analyses (list/get/del)│
│  • Dark/Light theme      │                │    /files/{id} (ETag + cache)  │
│  • Persistent history    │                │                                │
│  • Error boundaries      │                │  ┌──────────────────────────┐  │
└──────────────────────────┘                │  │  PyTorch + smp.Unet      │  │
                                            │  │  (best_model.pth)        │  │
                                            │  └──────────────────────────┘  │
                                            │  ┌──────────────────────────┐  │
                                            │  │  SQLite (default)        │  │
                                            │  │  / Postgres (opt-in)     │  │
                                            │  │  via SQLModel            │  │
                                            │  └──────────────────────────┘  │
                                            └────────────────────────────────┘
                                                          ▲
                                                          │ imports
                                                          ▼
                                            ┌────────────────────────────────┐
                                            │  src/  — ML research pipeline  │
                                            │  train · infer · eval · etc.   │
                                            └────────────────────────────────┘
```

---

## Quickstart — under 5 minutes

```bash
# 1. clone + venv
git clone <repo-url> nuclei-ai && cd nuclei-ai
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 2. install
pip install -r requirements.txt

# 3. configure
cp .env.example .env

# 4. run backend
uvicorn backend.main:app --reload --port 8000

# 5. in another terminal — run frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, click **Sign in** (any email works), navigate to
**New Analysis**, and click any of the **demo thumbnails** to instantly run a
real prediction. Refresh the page — your analysis is still there.

> No GPU is required. All numbers in this README were captured on CPU.

---

## API at a glance

| Method | Path | Purpose |
|---|---|---|
| `GET`    | `/api/health`              | Model load status, device, mode (`model` / `fallback-demo`) |
| `POST`   | `/api/analyze`             | Upload an image, get back masks, overlay, count, metadata |
| `GET`    | `/api/analyses`            | Paginated list of persisted analyses (newest first) |
| `GET`    | `/api/analyses/{job_id}`   | Single analysis as stored in the DB |
| `DELETE` | `/api/analyses/{job_id}`   | Permanently delete a job + result row |
| `GET`    | `/files/{filename}`        | Cached static delivery of input/mask/overlay images |

Every response carries an `X-Request-ID` header. Every request emits a
single-line JSON log record with `request_id`, `method`, `path`, `status`,
`duration_ms`, and `client`.

Interactive Swagger UI: `http://127.0.0.1:8000/docs`.

---

## Reported metrics

Trained on 29 images, validated on 4, tested on 4 (held-out).

| Split | Dice | IoU | Counting MAE | Counting MSE |
|---|---:|---:|---:|---:|
| Validation | **0.7414** | **0.5902** | **70.75** | 6849.75 |
| Test (held-out) | 0.3787 | 0.2752 | 214.00 | 58 357.50 |

Test-set numbers are dominated by a single failure tile (TCGA-G9-6363, Dice ≈ 0).
Section 9.4 of [docs/FINAL_REPORT_DRAFT.md](docs/FINAL_REPORT_DRAFT.md)
discusses this honestly and treats the 4-image average as a *trend indicator*
rather than a population estimate.

---

## Project layout

```text
project/
├── backend/                    FastAPI service
│   ├── main.py                 routes, middleware, lifespan
│   ├── config.py               pydantic-settings .env loader
│   ├── logging_config.py       structured JSON logging
│   ├── rate_limit.py           per-IP token bucket
│   ├── schemas.py              pydantic models for requests/responses
│   ├── services/               analysis_service.py
│   ├── db/                     SQLModel models, session, repositories, init_db
│   └── alembic/                Postgres migration (preserved for prod use)
├── frontend/                   React 18 + Vite + Tailwind
│   ├── src/pages/              Dashboard, NewAnalysis, AnalysisResult,
│   │                           AnalysisHistory, Reports, Settings, AiChat,
│   │                           Login, NotFound
│   ├── src/components/         UploadPanel, ResultViewer, WorkflowSteps,
│   │                           MetricCard, DemoStrip, ThemeToggle,
│   │                           ErrorBoundary, ui/
│   ├── src/layout/             Sidebar (NavLink), TopHeader, DashboardLayout
│   ├── src/lib/                historyStore.ts, theme.ts
│   ├── src/api.ts              typed HTTP client
│   └── public/demo/            bundled sample images for Demo Mode
├── src/                        ML pipeline
│   ├── train.py                argparse-driven; SaveBest by val Dice
│   ├── infer.py                argparse-driven single-image inference
│   ├── eval_test_set.py        Dice + IoU + counting on the held-out split
│   ├── batch_count_refined.py  XML-GT counting (selected pipeline)
│   ├── tune_threshold_xmlgt.py threshold sweep
│   ├── extract_morphology.py   per-nucleus shape features
│   ├── generate_density_maps.py density heatmaps
│   ├── model_registry.py       file-backed run registry
│   ├── dataset.py · metrics.py · postprocess.py · xml_to_masks.py · ...
│   └── app.py                  Streamlit research dashboard (read-only)
├── tests/                      pytest integration suite (20 tests, 100% pass)
├── docs/                       SAD, role assignment, plans, design concept,
│                               FINAL_REPORT_DRAFT.md
├── data/splits/                train.csv · val.csv · test.csv · all.csv
├── outputs/                    checkpoints, masks, overlays, evaluations
├── README.md · LICENSE · CHANGELOG.md · CONTRIBUTING.md
└── requirements.txt · package.json · docker-compose.yml · alembic.ini
```

---

## Configuration

All knobs live in `.env`. See [.env.example](.env.example) for the full list.
Highlights:

| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | _(unset → SQLite)_ | Set to a Postgres URL for production |
| `THRESHOLD` | `0.7` | Selected operating point — lowest counting MAE |
| `MIN_AREA` | `5` | Connected-components noise filter |
| `MAX_UPLOAD_BYTES` | `52428800` | 50 MB |
| `RATE_LIMIT_UPLOAD_PER_MINUTE` | `5` | Per-IP cap on `/api/analyze` |
| `MODEL_CHECKPOINT` | `outputs/checkpoints/best_model.pth` | Inference weights |
| `ALLOWED_ORIGINS` | localhost:5173 | CORS allow-list |

If the checkpoint is missing or fails to load, the API automatically falls
back to an Otsu-threshold demo mode so the UI is always testable end-to-end.

---

## Development

```bash
# Backend tests
pytest -q

# Frontend typecheck
cd frontend && npm run typecheck

# Train (CPU friendly)
python -m src.train --epochs 5 --batch-size 2

# Single-image inference
python -m src.infer --image data/processed/images/<name>.png

# Full evaluation
python -m src.eval_test_set
python -m src.batch_count_refined
python -m src.tune_threshold_xmlgt

# Streamlit research dashboard (separate UI, reads precomputed outputs)
streamlit run src/app.py
```

---

## Roadmap

- [ ] Background job queue with progress streaming (SSE / WebSocket).
- [ ] JWT-based authentication on top of the existing `users` table.
- [ ] S3-compatible object storage abstraction for `backend/storage/`.
- [ ] Watershed/instance segmentation experiments to recover dense-cluster cases.
- [ ] Larger training corpus + cross-validation reporting.
- [ ] Playwright E2E tests in CI.

---

## Acknowledgements

- **Dataset:** [MoNuSeg](https://monuseg.grand-challenge.org/) — annotated histopathology nuclei from TCGA.
- **Model:** [segmentation_models_pytorch](https://github.com/qubvel/segmentation_models.pytorch) U-Net with ResNet-18 encoder.
- **UI inspiration:** glassmorphism design language defined in [docs/UI_3D_DESIGN_CONCEPT.md](docs/UI_3D_DESIGN_CONCEPT.md).

This project was developed for **ENS 005 — Application of AI in Image Processing**.
