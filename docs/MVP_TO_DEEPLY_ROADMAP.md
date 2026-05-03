# MVP → Deeply Analytics — Migration Roadmap

> **Purpose.** A file-by-file map from the current working MVP to the Deeply Analytics target architecture. It exists so the team can plan the migration without re-reading both long documents (`DEEPLY_ANALYTICS_FULL_SYSTEM_SPEC.md`, `DEEPLY_ANALYTICS_ANIMATION_AND_INTEGRATION_GUIDE.md`).
>
> **Companion documents.** Read this alongside [`DEEPLY_ANALYTICS_FULL_SYSTEM_SPEC.md`](DEEPLY_ANALYTICS_FULL_SYSTEM_SPEC.md) (architecture) and [`DEEPLY_ANALYTICS_ANIMATION_AND_INTEGRATION_GUIDE.md`](DEEPLY_ANALYTICS_ANIMATION_AND_INTEGRATION_GUIDE.md) (boundary contracts and animation recipes).
>
> **Status legend.** **[Implemented]** = verified in the repository today · **[Partial]** = exists in skeletal form · **[Proposed]** = part of the target architecture, not yet built.
>
> **Document version.** v0.1 — 2026-05-02.

---

## 1. Repository snapshot today

```
project/
├── src/                           AI module (Implemented)
├── outputs/                       Generated artefacts + trained checkpoint (Implemented)
├── data/                          Datasets and splits (Implemented)
├── notebooks/, reports/           Empty
├── backend/                       FastAPI MVP (Partial)
│   ├── main.py                    /api/health, /api/analyze, /files/{name}
│   ├── schemas.py                 Health/Analysis Pydantic models
│   ├── services/
│   │   └── analysis_service.py    Wraps src.infer + src.batch_count_refined
│   └── storage/
│       ├── uploads/               Local FS uploads
│       └── results/               Local FS masks/overlays
├── frontend/                      React + Vite + TS MVP (Partial)
│   └── src/
│       ├── App.tsx                Single-page dashboard
│       ├── main.tsx
│       ├── api.ts
│       ├── styles.css             3D-inspired tokens
│       └── components/
│           ├── UploadPanel.tsx
│           ├── ResultViewer.tsx
│           ├── WorkflowSteps.tsx
│           └── MetricCard.tsx
├── docs/                          Documentation (this folder)
├── .venv/                         Python venv
├── requirements.txt
└── README.md
```

## 2. Backend file-by-file mapping

The MVP backend is a flat module under `backend/`. The target backend is layered: **routers → services → repositories → DB / storage / AI**.

| Today (MVP) | Status | Target (Deeply Analytics) | Migration action |
|---|---|---|---|
| `backend/main.py` | [Partial] | `backend/main.py` (app factory only) + `backend/routers/*.py` | Split routes out: extract `/api/health` → `routers/health.py`, `/api/analyze` → `routers/analyses.py`, `/files/{name}` → `routers/files.py`. Keep `main.py` as `create_app()` that mounts routers + middleware. |
| `backend/schemas.py` | [Implemented] (3 models) | `backend/schemas/{health.py, auth.py, projects.py, analyses.py, results.py, exports.py}` | Move existing `HealthResponse`, `AnalysisResponse`, `AnalysisMetadata` into `schemas/health.py` and `schemas/analyses.py`. Add new schemas for the rest as those routers are built. |
| `backend/services/analysis_service.py` | [Partial] (single `analyze()` fn) | `backend/services/analysis_service.py` (service class, multiple methods) + `backend/services/{auth,project,result,export}_service.py` | Convert the module-level functions to a class with constructor-injected dependencies (`session`, `storage`, `model_registry`). Methods: `create_job`, `process_job`, `get_status`, `get_result`. Adds: project ownership check, DB write of `analysis_jobs` row before enqueue. |
| `backend/services/__init__.py` | [Implemented] | Same path | Keep. |
| `backend/__init__.py` | [Implemented] | Same path | Keep. |
| (none) | [Proposed] | `backend/config.py` | Create `Settings` class with `pydantic-settings`; reads env vars (DB URL, JWT secret, storage root, S3 creds, rate limits, max upload size). |
| (none) | [Proposed] | `backend/db/session.py`, `backend/db/base.py` | SQLAlchemy/SQLModel engine + `get_session` dependency. |
| (none) | [Proposed] | `backend/db/models/{user,project,analysis_job,analysis_result,morphology_record,export}.py` | One file per table, matching the schema in spec section G. |
| (none) | [Proposed] | `backend/db/repositories/{users,projects,analyses,results,morphology,exports}.py` | Thin repository classes; one method per query. |
| (none) | [Proposed] | `backend/dependencies/auth.py` | `current_user`, `require_role`, `get_session` FastAPI dependencies. |
| (none) | [Proposed] | `backend/middleware/{cors,rate_limit,size_limit}.py` | Move CORS config out of `main.py` into a middleware module; add `slowapi` rate limiter; enforce 25 MB upload cap. |
| `backend/main.py` (CORS allowlist) | [Implemented] | `backend/middleware/cors.py` | Reuse the allowlist; extend with prod origins from `Settings.allowed_origins`. |
| (none) | [Proposed] | `backend/workers/{runner.py,tasks.py}` | Celery app + tasks. For Phase 1 use FastAPI `BackgroundTasks` first; promote to Celery in Phase 2. |
| (none) | [Proposed] | `backend/storage/object_storage.py` | `ObjectStorage` interface + `LocalFsStorage` (today) and `S3Storage` (prod). The DB stores keys; routes mint signed URLs. |
| `backend/storage/uploads/` | [Implemented] | `backend/storage/uploads/` (dev only) → S3 bucket `uploads/` (prod) | Keep folder for local dev; production reads/writes via `ObjectStorage`. |
| `backend/storage/results/` | [Implemented] | Same pattern | Same. |
| (none) | [Proposed] | `backend/exceptions/domain.py` + handler in `main.py` | `NotFound`, `Forbidden`, `Conflict`, `ValidationError` → mapped to HTTP codes by a single global handler. |
| (none) | [Proposed] | `alembic/`, `alembic.ini` | Migration root; first migration creates the 6 core tables. |
| (none) | [Proposed] | `tests/backend/` (pytest) | Per-router integration suites; transactional fixtures. |

### Resulting target tree

```
backend/
├── main.py                       # create_app() only
├── config.py
├── exceptions/domain.py
├── middleware/
│   ├── cors.py
│   ├── rate_limit.py
│   └── size_limit.py
├── dependencies/auth.py
├── routers/
│   ├── auth.py
│   ├── projects.py
│   ├── analyses.py
│   ├── results.py
│   ├── reports.py
│   ├── files.py
│   └── health.py
├── schemas/
│   ├── auth.py
│   ├── projects.py
│   ├── analyses.py
│   ├── results.py
│   ├── exports.py
│   └── health.py
├── services/
│   ├── auth_service.py
│   ├── project_service.py
│   ├── analysis_service.py        # current MVP grows into this
│   ├── result_service.py
│   └── export_service.py
├── db/
│   ├── base.py
│   ├── session.py
│   ├── models/
│   └── repositories/
├── workers/
│   ├── runner.py
│   └── tasks.py
├── storage/
│   ├── object_storage.py
│   ├── uploads/                   # dev only
│   └── results/                   # dev only
└── alembic/
```

## 3. Frontend file-by-file mapping

The MVP frontend is a single-page dashboard. The target is a 7-page SaaS dashboard with auth, routing, animation, and a typed API client.

| Today (MVP) | Status | Target (Deeply Analytics) | Migration action |
|---|---|---|---|
| `frontend/src/main.tsx` | [Implemented] | `frontend/src/main.tsx` | Wrap with `<BrowserRouter>`, `<QueryClientProvider>`, `<MotionConfig reducedMotion="user">`, `<AuthProvider>`. |
| `frontend/src/App.tsx` (single page) | [Partial] | `frontend/src/App.tsx` (shell only) + `frontend/src/routes.tsx` + `frontend/src/pages/*` | Move shell to `components/layout/AppShell.tsx`; replace App body with the route tree. Today's analyze flow becomes the `NewAnalysis` page. |
| `frontend/src/api.ts` | [Implemented] (1 endpoint) | `frontend/src/api/{client.ts, auth.ts, projects.ts, analyses.ts, results.ts, reports.ts}` | Promote `client.ts` to JWT-injecting wrapper; split per resource. The current `analyzeImage()` becomes `analyses.upload()`. |
| `frontend/src/styles.css` (3D tokens) | [Implemented] | `frontend/src/styles/{tokens.css, layout.css, components.css}` | Keep tokens; split layout/component rules out as the surface grows. |
| `frontend/src/components/UploadPanel.tsx` | [Implemented] | `frontend/src/components/upload/UploadPanel.tsx` | Move under feature folder; promote to use `react-hook-form` for validation. |
| `frontend/src/components/ResultViewer.tsx` | [Implemented] | `frontend/src/components/result/ResultViewer.tsx` + `ResultTabs.tsx` + `OverlayTile.tsx` + `MaskTile.tsx` + `DensityTile.tsx` | Split the three image tiles + KPI tiles into smaller components for reuse on the History detail view. |
| `frontend/src/components/WorkflowSteps.tsx` | [Implemented] | `frontend/src/components/workflow/WorkflowSteps.tsx` | Add Framer Motion `active`/`done` variants per recipe in the Animation Guide. |
| `frontend/src/components/MetricCard.tsx` | [Implemented] | `frontend/src/components/kpi/MetricCard.tsx` + `KpiGrid.tsx` | Add staggered reveal via `motion.ts` variants; reused on Dashboard, Result, History detail. |
| (none) | [Proposed] | `frontend/src/pages/Login.tsx` | Email + password form; calls `auth.login()`; stores JWT; redirects to Dashboard. |
| (none) | [Proposed] | `frontend/src/pages/Dashboard.tsx` | KPI grid (total analyses, processed cells, avg processing time), recent jobs table. |
| (none) | [Proposed] | `frontend/src/pages/NewAnalysis.tsx` | Today's MVP UI (UploadPanel + WorkflowSteps + ResultViewer) wrapped as a routed page; project picker added. |
| (none) | [Proposed] | `frontend/src/pages/AnalysisResult.tsx` | Tabs `Overlay | Mask | Density | Morphology`; animated count; layoutId tab underline. |
| (none) | [Proposed] | `frontend/src/pages/AnalysisHistory.tsx` | Filterable, paginated table; row click → `AnalysisResult`. |
| (none) | [Proposed] | `frontend/src/pages/Reports.tsx` | Export modal (CSV / PNG / PDF); list of past exports with download links. |
| (none) | [Proposed] | `frontend/src/pages/Settings.tsx` | Profile + account; admin sub-tab gated by `require_role("admin")`. |
| (none) | [Proposed] | `frontend/src/components/layout/{AppShell.tsx, Sidebar.tsx, Header.tsx}` | Fixed sidebar (collapsible on mobile), top header with user menu. |
| (none) | [Proposed] | `frontend/src/auth/{AuthContext.tsx, RequireAuth.tsx}` | Token storage + guarded routes. |
| (none) | [Proposed] | `frontend/src/hooks/{useAnalysisJob.ts, useAuth.ts, usePagination.ts}` | TanStack Query–powered hooks with polling for in-progress jobs. |
| (none) | [Proposed] | `frontend/src/lib/motion.ts` | Shared Framer Motion variants (per Animation Guide section 2.4). |
| (none) | [Proposed] | `frontend/src/types/api.ts` | Generated from FastAPI OpenAPI via `openapi-typescript`. |
| (none) | [Proposed] | `frontend/tests/e2e/` (Playwright) | Login, upload, result, history, export flows. |

### Resulting target tree

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx                   # shell + routes only
│   ├── routes.tsx
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── projects.ts
│   │   ├── analyses.ts
│   │   ├── results.ts
│   │   └── reports.ts
│   ├── auth/
│   │   ├── AuthContext.tsx
│   │   └── RequireAuth.tsx
│   ├── hooks/
│   │   ├── useAnalysisJob.ts
│   │   └── useAuth.ts
│   ├── lib/
│   │   └── motion.ts
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── NewAnalysis.tsx
│   │   ├── AnalysisResult.tsx
│   │   ├── AnalysisHistory.tsx
│   │   ├── Reports.tsx
│   │   └── Settings.tsx
│   ├── components/
│   │   ├── layout/{AppShell, Sidebar, Header}.tsx
│   │   ├── upload/UploadPanel.tsx
│   │   ├── workflow/WorkflowSteps.tsx
│   │   ├── result/{ResultViewer, ResultTabs, OverlayTile, MaskTile, DensityTile}.tsx
│   │   └── kpi/{MetricCard, KpiGrid}.tsx
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── layout.css
│   │   └── components.css
│   ├── types/
│   │   └── api.ts
│   └── tests/e2e/
```

## 4. AI module mapping

The `src/` tree is the AI implementation. **It will not be moved**; the backend service layer imports from it. The mapping below shows where each script fits in the spec's AI inference layer (section J).

| Today (`src/`) | Status | Spec module | Migration action |
|---|---|---|---|
| `src/infer.py` (`load_image`, `make_overlay`, `main`) | [Implemented] | `preprocess.py` (`load_image`) + `infer.py` (`predict`) + `postprocess.py` (`make_overlay`) | Wrap in `backend/services/analysis_service.py`; **do not split the file in `src/`** — the backend imports the helpers it needs. |
| `src/batch_count_refined.py` (`count_nuclei_from_binary`) | [Implemented] | `count.py` | Already imported by the MVP service. Keep. |
| `src/extract_morphology.py` | [Implemented] | `morphology.py` | Wire in `result_service.compute_morphology(job_id)`; persist rows in `morphology_records`. |
| `src/generate_density_maps.py` | [Implemented] | `density.py` | Wire in `result_service.compute_density(job_id)`; write PNG to storage. |
| `src/postprocess.py` | [Partial] | `postprocess.py` | Promote thresholding + connected-component logic into a clean public function used by both single and batch flows. |
| `src/dataset.py`, `src/train.py`, `src/metrics.py` | [Implemented] | Training utilities (out of API path) | Keep in `src/`; not called by the API. |
| `src/tune_min_area.py`, `src/tune_threshold_xmlgt.py` | [Implemented] | Hyperparameter scripts (out of API path) | Keep. |
| `src/xml_to_masks.py`, `src/make_splits.py`, `src/make_all_csv.py`, `src/extract_gt_counts.py` | [Implemented] | Data-prep scripts (out of API path) | Keep. |
| `src/app.py` (Streamlit prototype) | [Implemented] | None — replaced by React app | Keep as a working reference until the React app reaches feature parity, then archive. |
| `src/utils.py`, `src/visualize.py` | [Partial] (empty) | TBD | Either fill or delete. Currently empty files; recommend deletion if they remain unused after Phase 2. |
| `outputs/checkpoints/best_model.pth` | [Implemented] | Loaded by the analysis service | Keep. Add `outputs/checkpoints/v{N}/` versioning when retrained. |
| `outputs/counting_batch_refined_xmlgt/`, `outputs/density_maps/`, `outputs/morphology/` | [Implemented] | Reference outputs (used by `src/app.py`) | Keep as historical reference. New per-job outputs go to `backend/storage/results/{job_id}/` (dev) or `s3://.../results/{job_id}/` (prod). |

**Dependency rule.** `backend → src` only. `src` never imports from `backend`. This keeps the AI module reusable by training scripts, notebooks, and the API.

## 5. Storage and database mapping

| Today | Status | Target | Migration action |
|---|---|---|---|
| `backend/storage/uploads/{job_id}.{ext}` | [Implemented] | Same path in dev; `s3://deeply/uploads/{job_id}.{ext}` in prod | Add `ObjectStorage` interface; switch backend by env var. |
| `backend/storage/results/{job_id}_{kind}.png` | [Implemented] | `backend/storage/results/{job_id}/{kind}.png` (dev) and `s3://deeply/results/{job_id}/{kind}.png` (prod) | Move to per-job folder layout for forward compatibility (density, exports, multiple variants). |
| `outputs/` (training + reference outputs) | [Implemented] | Unchanged | Read-only at runtime. |
| (none — no DB today) | [Proposed] | PostgreSQL: `users`, `projects`, `analysis_jobs`, `analysis_results`, `morphology_records`, `exports` | First Alembic migration creates all six tables; foreign keys per spec section G. |
| Job state today (synchronous, in-memory) | [Implemented] | `analysis_jobs.status` in PostgreSQL (`pending → processing → completed | failed`) | Status transitions written by the worker; surfaced via `/analyses/{id}/status`. |
| Result metadata today (only in HTTP response) | [Implemented] | `analysis_results` rows + linked `morphology_records` rows | After inference, the worker persists structured results; the response endpoint reads from DB, not from in-memory state. |
| Per-nucleus morphology today (CSV in `outputs/morphology/`) | [Implemented] (batch only) | `morphology_records` rows, one per nucleus per job | Bulk insert at the end of the job; no CSV in the live path (CSV becomes an export format). |
| Exports today (none) | [Proposed] | `exports` table + `s3://deeply/exports/{export_id}.{format}` | New table records what was exported, when, by whom; the file lives in storage. |

**The principle.** PostgreSQL stores **structured metadata and references**. Object storage stores **binary artefacts**. The DB never holds image bytes; storage never holds queryable structured data.

## 6. Implementation status snapshot (one table)

| Capability | MVP | Deeply Analytics target |
|---|---|---|
| U-Net inference on uploaded image | [Implemented] | Same (wrapped in service) |
| Overlay + mask + density + morphology generation | [Implemented] (single + batch scripts) | Same, called by the analysis worker |
| Local file storage | [Implemented] | Dev only; S3 in prod |
| FastAPI app with CORS | [Implemented] | Same, expanded |
| Single `/api/analyze` endpoint | [Implemented] | Replaced by `/analyses/upload`, `/analyses/start`, `/analyses/{id}/status`, `/analyses/{id}` |
| Synchronous inference inside the request | [Implemented] | Background tasks (Phase 1) → Celery (Phase 2) |
| Single-page React UI | [Implemented] | 7 pages with auth, routing, layout |
| 3D-inspired CSS tokens | [Implemented] | Same tokens, expanded with motion via Framer Motion |
| User accounts | [Proposed] | `users` table + JWT + `RequireAuth` |
| Projects + history | [Proposed] | `projects`, `analysis_jobs` + History page |
| Authorisation (owner-only resource access) | [Proposed] | Service-level checks on every read/write |
| RBAC (admin) | [Proposed] | `require_role("admin")` |
| Rate limiting | [Proposed] | `slowapi` per-endpoint |
| Exports (CSV / PNG / PDF) | [Proposed] | `exports` table + Reports page |
| pytest backend suite | [Proposed] | Per-router integration tests |
| Playwright E2E suite | [Proposed] | Login, upload, result, history, export |
| Vercel + Railway deployment | [Proposed] | Containerised backend; managed Postgres + Redis + S3 |
| Animation system (Framer Motion) | [Proposed] | Per Animation Guide |

## 7. Recommended migration order

The order minimises rework. Each step is independently shippable.

### Phase 1 — Foundations (DB + auth + persistent jobs)

1. **`backend/config.py`.** Move CORS allowlist, max upload size, threshold, min_area, checkpoint path into `Settings`. No behaviour change.
2. **`backend/db/`.** Add SQLModel/SQLAlchemy session, base, and the first model: `users`. First Alembic migration. Local Postgres via Docker compose for dev.
3. **Auth slice.** `services/auth_service.py` (hash with argon2, mint JWT), `routers/auth.py` (`/register`, `/login`, `/me`), `dependencies/auth.py` (`current_user`).
4. **Frontend auth slice.** `pages/Login.tsx`, `auth/AuthContext.tsx`, `auth/RequireAuth.tsx`, `api/client.ts` JWT injection. Wrap existing single-page UI in `RequireAuth`.
5. **`projects` and `analysis_jobs` tables.** Models + migrations + repositories. Service: `project_service.create / list / get_owned`.
6. **Persist jobs.** Refactor `services/analysis_service.py`:
   - `create_job(file, project_id, params, user) -> Job` — saves upload, inserts `analysis_jobs` row with `status="pending"`, returns the row.
   - `process_job(job_id)` — runs the pipeline (current MVP code), writes `analysis_results`, updates status. Triggered via `BackgroundTasks` for Phase 1.
   - `get_status(job_id, user)`, `get_result(job_id, user)`.
7. **New routes.** `routers/analyses.py` (`upload`, `start`, `status/{id}`, `{id}`, `history`). Keep `/api/analyze` as a deprecated alias for one release.
8. **Frontend routing tree.** `routes.tsx`, `AppShell`, `Sidebar`, `Header`, blank skeletons for the 7 pages. Move today's UI into `pages/NewAnalysis.tsx`.
9. **Dashboard page.** KPI grid + recent jobs table powered by `/analyses/history`. First Framer Motion staggered reveal.
10. **History page.** Same data with filters and pagination.

### Phase 2 — Result depth + exports + polish

11. **Result depth tables.** `analysis_results` columns expanded (cell_count, processing_ms, mode, model_version), `morphology_records` table. Worker computes and persists.
12. **Routes.** `routers/results.py` (`/results/{id}/overlay|mask|density|morphology`).
13. **Frontend `AnalysisResult` page.** Tabs (Overlay / Mask / Density / Morphology); animated count; layoutId tab underline; cross-fade.
14. **Exports.** `exports` table + `services/export_service.py` (CSV, PNG, PDF). `routers/reports.py`. Frontend `Reports.tsx` with export modal + success toast.
15. **Authorisation tightening.** Owner-only checks on every read; `require_role("admin")` on Settings → Admin sub-tab; rate limiting on `/auth/login` and `/analyses/upload`.
16. **Object storage abstraction.** `ObjectStorage` interface; `LocalFsStorage` + `S3Storage`. Switch via `Settings.storage_bucket`.
17. **Background workers (production).** Move `process_job` from `BackgroundTasks` to Celery + Redis. Two queues: `inference` and `default`.
18. **Animation polish.** Wire `lib/motion.ts`, `MotionConfig reducedMotion="user"`, the 12 recipes from the Animation Guide.
19. **Tests.** pytest per router (auth, projects, analyses, results, reports); Playwright E2E for login, upload, result, history, export.
20. **Deployment.** Vercel for `frontend/`; backend Dockerfile + Railway/Render service; managed Postgres + Redis + S3; smoke-test staging; promote to prod.

### Stop-line: do not skip these

- **Step 6 before step 7.** The `analyses.py` router cannot exist without the persisted job model.
- **Step 8 before step 9.** The Dashboard depends on the route tree.
- **Step 16 before step 20.** Local FS will not survive multi-instance backend deployment.

## 8. What does NOT change

- The `src/` AI module file layout. It is imported, not moved.
- The trained checkpoint at `outputs/checkpoints/best_model.pth`.
- The dataset and splits in `data/`.
- The reference outputs in `outputs/`.
- The Streamlit prototype at `src/app.py` — kept until the React app reaches parity.
- The `requirements.txt` and `README.md` (until the deployment phase).
- The documentation set in `docs/` — only this file is added.

## 9. Open decisions to resolve before Phase 1 starts

1. **SQLModel vs SQLAlchemy 2.x + Pydantic.** Both work. The team picks one and commits.
2. **Cookies vs `localStorage` for the JWT.** HTTP-only cookies are safer (XSS-resistant); `localStorage` is simpler. Pick before building the auth slice.
3. **Background task runner for Phase 1.** `BackgroundTasks` is enough to ship; Celery is the production answer. Confirm we are happy to swap once during Phase 2.
4. **Storage backend for prod.** R2, Spaces, Backblaze, MinIO, S3 — all S3-compatible. Pick before step 16.
5. **Pricing model.** Out of scope for this document, but it influences whether `users.tier` and quota fields are needed in Phase 1 or Phase 2.

---

*End of roadmap. Pair with `DEEPLY_ANALYTICS_FULL_SYSTEM_SPEC.md` (architecture) and `DEEPLY_ANALYTICS_ANIMATION_AND_INTEGRATION_GUIDE.md` (boundary contracts and animation recipes).*
