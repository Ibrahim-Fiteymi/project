# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows [SemVer](https://semver.org/) where reasonable.

## [0.3.0] — 2026-05-08

Productisation pass: the project now runs end-to-end with persistent history,
structured logging, rate limiting, ETag caching, real tests, and a polished
React UI with a dark/light toggle and one-click demo mode.

### Added
- **Persistent history** — `/api/analyses` (GET, list), `/api/analyses/{id}` (GET, DELETE).
  SQLite default at `backend/storage/deeply.db`; Postgres opt-in via `DATABASE_URL`.
- **Repositories layer** ([backend/db/repositories.py](backend/db/repositories.py)) — clean separation between the service and SQL.
- **System user + default project** auto-seeded on first startup.
- **Structured JSON logging** ([backend/logging_config.py](backend/logging_config.py)) — request id, method, status, duration on every request.
- **Rate limiter** ([backend/rate_limit.py](backend/rate_limit.py)) — per-IP token bucket on `/api/analyze`. Default 5/min, configurable via `RATE_LIMIT_UPLOAD_PER_MINUTE`.
- **ETag + Cache-Control** on `/files/*` for browser caching.
- **Pydantic input validation** — content-type and extension whitelist on uploads. Limit raised to 50 MB. 413 on oversize, 415 on unsupported types.
- **Test-set evaluation** — new [src/eval_test_set.py](src/eval_test_set.py); per-image Dice, IoU, MAE, MSE.
- **React Router 6** — true URL-driven navigation, back/forward, deep linking.
- **ErrorBoundary + NotFound** routes — friendly recovery UI.
- **Demo mode strip** on New Analysis — three sample images, one click.
- **Theme toggle** in the top header — dark (default) / light.
- **Mobile responsive** layout — sidebar collapses to top strip below 900 px.
- **Skeleton loaders, page transitions, history thumbnails, danger button styles**.
- **Model registry** ([src/model_registry.py](src/model_registry.py)) — versioned checkpoints, `registry.json` with hyperparameters and metrics, automatic `best_model.pth` refresh.
- **Pytest integration suite** — 20 tests covering health, analyze success, persistence, validation, ETags, rate limiting, path traversal, concurrency.
- **Argparse on `train.py` and `infer.py`** — no hardcoded paths.

### Changed
- **Threshold standardised at τ = 0.7** across `.env`, `backend/config.py`, `src/batch_count_refined.py`, `src/infer.py`, `src/app.py`, `src/make_report4_dashboard.py` — matches the operating point reported in `FINAL_REPORT_DRAFT.md`.
- **MIN_AREA standardised at 5** across the entire pipeline.
- **`requirements.txt`** regenerated as ASCII (was UTF-16 mojibake) — `pip install` now works.
- **DB schema portability** — `analysis_jobs.parameters` now uses generic SQLAlchemy `JSON` instead of Postgres-specific `JSONB`, so the same model works on SQLite and Postgres.
- **`/api/analyze`** now returns 413 for oversize, 415 for unsupported MIME / extension, 429 for rate-limit.
- **Upload limit** 25 MB → 50 MB.
- **Frontend `historyStore`** is now backend-backed; `localStorage` is a fallback only.

### Removed
- `src/batch_count.py` — superseded by `batch_count_refined.py`.
- `src/batch_count_watershed.py` — rejected variant (MAE 111.8 vs 70.75).
- `src/utils.py`, `src/visualize.py` — empty stubs.

### Fixed
- Threshold mismatch between FINAL_REPORT_DRAFT.md (claimed τ = 0.7) and code (was running τ = 0.8).
- DATABASE_URL pointing at unreachable Postgres caused a 30-second hang on first request.

### Documentation
- New [README.md](README.md) — banner, badges, architecture diagram, 5-minute quickstart, full API table.
- New [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md).
- New Section 9.4 in [docs/FINAL_REPORT_DRAFT.md](docs/FINAL_REPORT_DRAFT.md): Held-out test-set results.
- Streamlit app ([src/app.py](src/app.py)) explicitly labelled a research dashboard; React frontend is the production UI.

## [0.2.0] — 2026-05-02
Initial dashboard scaffold: React + Vite frontend, Tailwind tokens, FastAPI backend with `/api/analyze` end-to-end against the trained U-Net.

## [0.1.0] — 2026-04-29
ML pipeline complete: U-Net training, inference, threshold tuning, density maps, morphology extraction, batch counting with XML ground truth.
