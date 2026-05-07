# Project Report — Draft

**AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting**

> Status legend used throughout this report: **[Implemented]** = verified in the current repository · **[Partial]** = exists in a prototype form · **[Proposed]** = part of the target academic architecture, not yet built.

---

## 1. Cover Page

| Field | Value |
|---|---|
| Project title | AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting |
| Course | Software Project Management & Technical Monitoring |
| Course code | _[to be filled]_ |
| Instructor | _[to be filled]_ |
| Semester / Academic year | _[to be filled]_ |
| Submission date | _[to be filled]_ |
| Team size | 4 members — **approved by the instructor** (course rule: 6–8; approval record in `INSTRUCTOR_APPROVAL_MESSAGE.md`, residual risk tracked in Section 15) |

**Team members and assigned roles**

| # | Name | Student ID | Role | Exact responsibilities |
|---|---|---|---|---|
| M1 | _[name]_ | _[id]_ | Project Manager + Risk Manager | Schedule, milestones, monitoring dashboards, risk register, stakeholder communication, instructor liaison |
| M2 | _[name]_ | _[id]_ | Lead Developer + Backend/API Lead | System architecture, FastAPI service, Pydantic schemas, SQLModel persistence, deployment to Railway |
| M3 | _[name]_ | _[id]_ | AI/ML Engineer + Data Processing Lead | U-Net training and inference, preprocessing, postprocessing, counting pipeline, model evaluation |
| M4 | _[name]_ | _[id]_ | UX/UI Designer + QA/Testing Lead | React+Vite+TS dashboard, 3D-inspired design system, pytest + Playwright suites, visual validation |

> A full breakdown of responsibilities, report contributions, presentation contributions, and monitoring duties is provided in `ROLE_ASSIGNMENT.md`.

---

## 2. Executive Summary

The AI-Powered Microscopy Analysis System is a web-based platform that helps biomedical researchers analyse microscopy images of cell nuclei. A user uploads a microscopy image; the system runs a U-Net deep learning model to segment the nuclei, applies post-processing, counts the cells, extracts morphological features, and returns visual outputs (overlays, masks, density heatmaps) together with a quantitative report.

The project is useful because manual nuclei counting is slow, subjective, and difficult to scale. By replacing the manual step with an AI pipeline, the system delivers consistent, repeatable measurements and frees researchers to focus on interpretation. From the perspective of this course, the project is also a vehicle to apply software project management and technical monitoring practices: progress is tracked through a management monitoring plan, and runtime behaviour is observed through a technical monitoring plan that watches API latency, inference duration, error rate, queue length, model availability, and uptime.

The current repository contains a working AI core — U-Net training, inference, counting, density-map generation, and morphology extraction **[Implemented]** — together with a FastAPI backend exposing `GET /api/health`, `POST /api/analyze`, and `GET /files/{filename}` **[Implemented MVP]** and a React + Vite + TypeScript multi-page dashboard (Login, Dashboard, New Analysis, Analysis Result, Analysis History, Reports, Settings) **[Implemented MVP]**. PostgreSQL persistence, JWT authentication, role-based access, real export automation, background job queues, an operational monitoring page, and production deployment to Vercel/Railway remain the **[Proposed]** target architecture for the academic plan.

---

## 3. Project Scope

### 3.1 In-scope features

- Microscopy image upload and storage **[Implemented MVP]** (file-system storage in `backend/storage/`; S3-compatible storage remains [Proposed])
- U-Net nuclei segmentation **[Implemented]**
- Connected-component cell counting **[Implemented]**
- Density heatmap generation **[Implemented]**
- Morphology feature extraction (area, circularity, eccentricity, etc.) **[Implemented]**
- Overlay and mask visualisation **[Implemented]**
- CSV / structured export of analysis results — AI-core CSV outputs in `outputs/` **[Implemented]**; the dashboard Reports page export buttons are **[Proposed]** placeholders, and one-click export automation is not wired
- Web dashboard — login page **[Implemented MVP — visual demo only, no real authentication]**
- Web dashboard — upload page **[Implemented]** (the New Analysis page)
- Web dashboard — analysis job status page **[Partial]** (in-page workflow stepper Upload → Segment → Count → Report; async job-status polling remains [Proposed])
- Web dashboard — results visualisation page **[Implemented]** (the Analysis Result page)
- Web dashboard — monitoring page **[Partial]** (the Dashboard page renders four KPI cards from session-local data; a full operational monitoring page remains [Proposed])
- Web dashboard — export / report page **[Partial]** (the Reports page exists with placeholder export cards; real export wiring remains [Proposed])
- Background inference jobs so the API does not block on long analyses **[Proposed]**
- JWT authentication, role-based access, rate limiting **[Proposed]**
- Management and technical monitoring dashboards **[Proposed]**
- 3D-inspired design language for the dashboard **[Partial]** (glassmorphism tokens, gradient accents, layered shadows, depth-tinted result tiles, and an Inter-based type scale are shipped in the live CSS; the isometric workflow illustration, hero illustration, and full Figma mockup set remain [Proposed])

### 3.2 Out-of-scope features

- Real-time microscope hardware integration
- Diagnostic / clinical decision-making (the system is a research tool, not a medical device)
- 3D volumetric microscopy reconstruction (z-stack)
- Multi-tenant billing and subscription management
- A full 3D rendering engine; the "3D design" is a 3D-inspired visual language, not WebGL geometry

### 3.3 Main users

- Biomedical and histopathology researchers analysing nuclei in tissue sections
- Laboratory technicians performing routine cell counts
- Course instructor and academic evaluators reviewing the project
- The development team itself, using the monitoring dashboards

### 3.4 System objectives

1. Reduce time spent on manual nuclei counting.
2. Produce repeatable, operator-independent counts and morphology metrics.
3. Expose the AI pipeline through a usable web interface.
4. Make project progress and system health observable through monitoring.
5. Demonstrate sound software engineering practice (layered architecture, validation, testing, deployment).

---

## 4. Problem Statement

Nuclei counting on microscopy images is a foundational measurement in histopathology and cell biology, yet in practice it is still done by hand or with semi-automated tools that require heavy operator tuning. Three problems follow:

1. **Manual counting is slow.** Annotation typically takes several minutes per image, which does not scale to studies that produce hundreds or thousands of fields of view (Ronneberger et al., 2015; Caicedo et al., 2019).
2. **Manual analysis is inconsistent.** Counts vary between observers and even between sessions of the same observer, which weakens downstream statistics.
3. **Researchers need faster and more reliable results** to iterate on experiments and meet publication timelines.

> **Acknowledged accuracy limit.** The current connected-component counter under-counts in regions of dense, touching nuclei. On the held-out evaluation set (37 images, XML ground truth), mean absolute error is approximately 277 cells per image. This limit is reflected in Section 5, in the technical monitoring quality gates (Section 12), and in risk #2 of `RISK_MANAGEMENT_PLAN.md`.

A fourth problem is internal to this course: the project itself must be **monitored**. Without a deliberate management monitoring plan, schedule slip and uneven workload are likely; without a technical monitoring plan, runtime regressions in the AI pipeline (slow inference, segmentation failures, queue back-pressure) are invisible until they cause user-facing failures.

---

## 5. Proposed Software Solution

The proposed solution is a web-based AI microscopy analysis platform with four interacting parts:

1. **A React + Vite + TypeScript multi-page dashboard** **[Implemented MVP]** with seven pages — Login, Dashboard, New Analysis, Analysis Result, Analysis History, Reports, Settings — that lets the researcher sign in (visual demo only), upload an image, follow the in-page workflow stepper, view results (overlay, mask, count, processing time), and browse local-session history. Real authentication, an operational monitoring page, and working export automation remain **[Proposed]**.
2. **A FastAPI service** **[Implemented MVP]** that exposes `GET /api/health`, `POST /api/analyze`, and `GET /files/{filename}`, validated by Pydantic models **[Implemented]**. Authentication endpoints, async job-status endpoints, project/history endpoints, and full RBAC remain **[Proposed]**.
3. **An AI processing layer** **[Implemented]** built around a PyTorch U-Net (ResNet18 encoder) that performs preprocessing, segmentation, thresholding, connected-component labelling, counting, and morphological feature extraction.
4. **A persistence and storage layer** **[Partial]** in which the local file system holds the binary artefacts (input images, masks, overlays) under `backend/storage/`. PostgreSQL with SQLModel + Alembic for structured metadata is **[Partial]** (models in `backend/db/models/` and a baseline Alembic migration exist; live database wiring remains **[Proposed]**), and S3-compatible object storage remains **[Proposed]**.

Long-running AI inference is dispatched to a background job runner so HTTP requests return quickly and the UI can poll job status. Both the management side and the technical side of the project are visible through monitoring surfaces (Section 11 and Section 12).

The current pipeline performs binary semantic segmentation followed by connected-component labelling. Because connected-component labelling cannot separate touching nuclei, the system under-counts in dense regions. This is the dominant source of error in the present implementation and is addressed by Section 12 (model-quality gates) and risk #2 in `RISK_MANAGEMENT_PLAN.md`.

---

## 6. Technology Stack and Platform Selection

| Layer | Technology | Status | Selection rationale |
|---|---|---|---|
| Frontend framework | React + Vite + TypeScript | [Implemented MVP] | Fast dev loop, typed components, mature ecosystem for SaaS dashboards |
| API framework | FastAPI | [Implemented MVP] | First-class async, automatic OpenAPI, native Pydantic integration |
| Validation | Pydantic | [Implemented] | Schema enforcement on requests, responses, and config |
| Architecture pattern | Layered (route → service → data) | [Partial] | Separation of concerns, testability, clear ownership; routes and a service module exist for the analyse path, broader layering remains [Proposed] |
| Database | PostgreSQL | [Proposed] | Relational integrity for users, jobs, and analysis records |
| ORM | SQLModel (over SQLAlchemy) | [Partial] | Models defined in `backend/db/models/`; live SQL session and repositories remain [Proposed] |
| Migration | Alembic | [Partial] | Baseline migration `20260502_0001_initial_schema.py` exists; no live database to migrate against yet |
| AI framework | PyTorch + segmentation_models_pytorch | [Implemented] | U-Net with ResNet18 encoder, Dice + BCE loss, validated checkpoint |
| Image / CV | OpenCV, scikit-image, PIL, NumPy | [Implemented] | Pre/postprocessing, connected components, morphology |
| Background jobs | Async task queue (e.g. Celery / RQ / FastAPI BackgroundTasks) | [Proposed] | Keeps API non-blocking during inference |
| Object/file storage | Local file system today; S3-compatible storage in production | [Partial] | The `outputs/` tree on the local file system is in active use as storage today (masks, overlays, density maps, morphology CSVs). "Partial" here means *file-on-disk works*; S3 has not been configured. |
| Testing — backend | pytest | [Proposed] | Unit and integration coverage |
| Testing — E2E | Playwright | [Proposed] | Browser-driven dashboard validation |
| Frontend deployment | Vercel | [Proposed] | Zero-config deploy for Vite/React |
| Backend deployment | Railway | [Proposed] | Simple PaaS for FastAPI + Postgres |
| Auth & security | JWT, RBAC, rate limiting, env-based secrets | [Proposed] | Standard SaaS security baseline |
| Prototype UI | Streamlit (`src/app.py`) | [Implemented] | Demoable interactive surface for the AI core today |

### 6.1 Current vs. target

The current code base implements the AI core, a FastAPI backend MVP (with `GET /api/health`, `POST /api/analyze`, and `GET /files/{filename}` endpoints validated by Pydantic), and a React + Vite + TypeScript multi-page dashboard MVP that talks to that backend. A Streamlit prototype (`src/app.py`) also exists as a developer-facing reference for the AI core, but the React dashboard is now the primary working demo surface. The remaining web-stack pieces — PostgreSQL with SQLModel + Alembic wired to a live database, JWT authentication and RBAC, background job queues, real export automation, Vercel/Railway deployment, and Playwright end-to-end coverage — are the **target** academic architecture and remain *Proposed*.

---

## 7. Software Design and Analysis Principles

| Principle | How the design honours it |
|---|---|
| **Maintainability** | Layered architecture; each layer has a single concern, so future changes (e.g. swapping the segmentation model) stay local. |
| **Scalability** | Stateless API, background workers, and object storage are designed so that additional worker instances can be added without schema changes. **[Proposed]** |
| **Cohesion** | The implemented modules in `src/` (training, inference, counting, density, morphology) each expose a single capability; the planned service and route layers will follow the same rule. |
| **Separation of concerns** | Routes handle HTTP, services orchestrate workflow, the data access layer talks to Postgres, the AI layer is pure inference. |
| **Modularity** | The AI pipeline is a sequence of replaceable stages; the frontend is a tree of small components. |
| **Reliability** | Background-job retries, schema validation at the boundary, and a technical monitoring plan that surfaces failures early. |
| **Testability** | Pure functions in the AI core, dependency-injected services, pytest for backend, Playwright for the dashboard. |

---

## 8. Architecture Overview

The proposed architecture is layered. Each layer has a single responsibility and a well-defined interface to the next.

```
┌──────────────────────────────────────────────────────┐
│ Frontend layer  (React + Vite + TS) [Implemented MVP]│
└──────────────────────────────────────────────────────┘
                  │  HTTPS (JSON; JWT proposed)
┌──────────────────────────────────────────────────────┐
│ API route layer  (FastAPI routers)  [Implemented MVP]│
└──────────────────────────────────────────────────────┘
                  │  validated DTOs (Pydantic)
┌──────────────────────────────────────────────────────┐
│ Service layer  (orchestration)              [Partial]│
└──────────────────────────────────────────────────────┘
       │                       │
┌──────────────┐      ┌──────────────────────┐
│ AI processing│      │ Data access layer    │
│ [Implemented]│      │ (SQLModel) [Partial] │
└──────────────┘      └──────────────────────┘
       │                       │
┌──────────────┐      ┌──────────────────────┐
│ Storage      │      │ Database (Postgres)  │
│ [Partial]    │      │ [Proposed]           │
└──────────────┘      └──────────────────────┘
                  │
┌──────────────────────────────────────────────────────┐
│ Monitoring layer (logs, metrics, dashboards)         │
│ [Proposed]                                           │
└──────────────────────────────────────────────────────┘
```

- **Frontend layer.** Renders pages, talks to the API over HTTPS, surfaces the partial 3D-inspired UI; the implemented MVP is a seven-page React + Vite + TS dashboard. JWT handling is **[Proposed]**.
- **API route layer.** FastAPI routers; the MVP exposes `GET /api/health`, `POST /api/analyze`, and `GET /files/{filename}` **[Implemented MVP]**, with Pydantic models guarding inputs and outputs. Routers per resource for auth, uploads, jobs, history, and monitoring are **[Proposed]**.
- **Service layer.** Orchestrates workflows: e.g. *receive image → persist metadata → enqueue inference → on completion, persist results → notify*. In the MVP the analysis service runs synchronously in-process; persistence and the enqueue/notify path are **[Proposed]**.
- **AI processing layer.** PyTorch U-Net, OpenCV postprocessing, connected-component counting, density and morphology computations.
- **Data access layer.** SQLModel models are defined in `backend/db/models/` **[Partial]**; live SQL session and repositories that hide SQL detail from services are **[Proposed]**.
- **Database layer.** PostgreSQL holds users, jobs, analysis records, audit metadata; Alembic migrations track schema. A baseline migration exists; live database wiring is **[Proposed]**.
- **Storage layer.** Local file system under `backend/storage/` holds the binary artefacts (input images, masks, overlays) today **[Partial]**; S3-compatible object storage and a separation in which the database holds references only are **[Proposed]**.
- **Monitoring layer.** Application logs, structured events, and metric exporters that feed a monitoring dashboard.

---

## 9. Basic UI / Dashboard Design

The dashboard is described page-by-page. The implemented MVP is a seven-page React + Vite + TypeScript application; visual language and 3D-inspired direction are detailed in `UI_3D_DESIGN_CONCEPT.md` and Section 10.

| Page | Status | Purpose | Key elements |
|---|---|---|---|
| **Login** | [Implemented MVP — visual demo only, no real authentication] | Show a sign-in surface and a route into the dashboard | Email + password fields, "Sign in" button that admits any non-empty email; explicit "Demo mode" label |
| **Dashboard** | [Implemented MVP] | Overview of analyses and system status | Four KPI cards (Total analyses, Completed, Avg cell count, Model status), Recent activity list, Quick actions; KPI data is sourced from session-local history |
| **New Analysis** | [Implemented] | Upload an image and run nuclei segmentation | Workflow stepper (Upload → Segment → Count → Report), drag-and-drop upload panel, inline result viewer, "View full result" hand-off |
| **Analysis Result** | [Implemented] | Standalone view of the most recent result | Original / mask / overlay tiles, cell count, processing time, mode badge |
| **Analysis History** | [Implemented MVP — uses local browser storage] | Past analyses run in this session | Table (date, file, cells, mode, time); falls back to clearly-labelled placeholder rows when empty; backend-backed history endpoints remain [Proposed] |
| **Reports / Export** | [Implemented MVP — placeholder] | Future export surface | Three disabled cards (CSV / PNG / PDF) with "Coming soon" badges; real export automation is [Proposed] |
| **Settings / Admin** | [Implemented MVP — placeholder] | Profile, model configuration, system settings | Three sections with read-only fields; placeholder labels make the lack of persistence explicit |

A future operational monitoring page (latency, error rate, queue length, recent failed jobs, model availability — see Section 12) is **[Proposed]**; the current Dashboard page covers a subset of these as session-local KPIs.

**Note on exports.** The AI core already produces structured CSV outputs (morphology summaries) under `outputs/` **[Implemented]**, but the Reports page export buttons in the dashboard are currently **placeholders**; wiring them to those AI-core CSVs and to a downloadable archive (CSV / PNG bundle / PDF) is **[Proposed]**.

A Streamlit prototype (`src/app.py`) **[Implemented]** also exists as a developer-facing reference for the AI core; the React + Vite + TS multi-page dashboard described above is now the primary working demo surface.

---

## 10. 3D Design Concept

This subsection summarises the 3D-inspired direction. The full specification is in `UI_3D_DESIGN_CONCEPT.md`.

- **Direction.** A 3D-inspired interface design language built on glassmorphism, depth, layered panels, soft shadow hierarchies, and isometric illustrations. It is **not** a 3D rendering engine.
- **Why 3D was selected.** Microscopy results are inherently visual; depth cues help the user separate the original image, the overlay, the heatmap, and the quantitative metrics. The same visual hierarchy supports clearer communication in the report and the in-class presentation.
- **Pages that use 3D-inspired elements.** Landing/hero, login, upload, analysis status, results, monitoring (see `UI_3D_DESIGN_CONCEPT.md` for per-page treatment).
- **How 3D improves visual communication.** Floating result cards, an isometric workflow diagram of the AI pipeline, layered panels in the monitoring dashboard, a 3D-style hero illustration on the landing page, and depth-tinted segmentation tiles all give evaluators an immediate read of the system.
- **Conceptual or implemented.** **Partial.** The CSS direction (glassmorphism tokens, gradient accents, shadow scale, layered panels, depth-tinted result tiles, responsive layout grid, Inter type scale) is now shipped in the live React + Vite + TS dashboard at `frontend/src/styles.css`. The broader 3D-inspired vision — the isometric workflow illustration, the hero illustration, and a full Figma mockup set — remains **proposed / conceptual** for this term.

---

## 11. Management Monitoring Plan

The full plan is in `MANAGEMENT_MONITORING_PLAN.md`. The headline metrics are:

- Task completion percentage, weekly milestone status, schedule variance
- Report completion progress, presentation preparation status
- Risk status, team workload distribution
- Submission readiness, video recording readiness

Each metric carries an owner (M1–M4), a tracking method, and a frequency. The Project Manager (M1) consolidates them in a weekly status report and raises any red items as risks.

---

## 12. Technical Monitoring Plan

The full plan is in `TECHNICAL_MONITORING_PLAN.md`. The runtime metrics are:

- API response latency, upload success rate
- Inference job duration, segmentation failure rate
- Background job queue length, error rate
- Storage usage, database health
- Model output availability, system uptime, authentication failure rate

Each metric carries a threshold and a monitoring method (application logs, structured metrics, scheduled health probes). The Backend/API Lead (M2) and the AI/ML Engineer (M3) co-own the runtime metrics; the QA Lead (M4) owns end-to-end smoke checks.

---

## 13. Value Creation Analysis

| Dimension | Value created |
|---|---|
| **Customer value** | Researchers get fast, repeatable nuclei counts and morphology features without manual tallying. |
| **Business value** | Lab throughput rises; a research group can process more images per dollar of analyst time. |
| **Functional value** | Single platform covers upload → analysis → visualisation → export, replacing a chain of ad-hoc scripts. |
| **Operational value** | Monitoring dashboards make project execution and system health observable, supporting the course's monitoring focus. |
| **Technical value** | Modular AI pipeline + layered backend make the system a reusable base for future microscopy tasks (other stains, other organs, other cell types). |

---

## 14. Stakeholder Management Plan

The full stakeholder map is in `STAKEHOLDER_MANAGEMENT_PLAN.md`. The seven groups are:

1. **Project team (M1–M4)** — owners and primary executors.
2. **Instructor** — academic evaluator and approver of the 4-member team configuration.
3. **Researchers / lab users** — primary end users.
4. **System administrator** — handles deployment and storage in production.
5. **AI developer** — owner of model accuracy and pipeline stability (M3).
6. **End users** — anyone running an analysis through the dashboard.
7. **University / academic evaluators** — review the report, presentation, and video.

---

## 15. Risk Management Framework

The full risk register is in `RISK_MANAGEMENT_PLAN.md`. The framework follows: **Identification → Assessment → Mitigation → Monitoring → Ownership.** The eleven tracked risks include:

1. **Team has only 4 members instead of 6–8** *(compliance item — **resolved**: the instructor approved the 4-member team in writing; roles are consolidated across four members; residual risk is Low and limited to workload distribution).*
2. AI model may not perform accurately enough on dense regions.
3. Dataset preprocessing may take longer than expected.
4. Backend inference may be slow.
5. UI dashboard may remain too basic.
6. 3D design may stay conceptual and not visualise clearly.
7. Integration between frontend, backend, AI module, database, and storage may fail.
8. Schedule overrun.
9. Technical debt.
10. Presentation exceeding 7 minutes.
11. Video link permission problem.

The 4-member compliance risk is the headline item and is paired with a written request to the instructor (`INSTRUCTOR_APPROVAL_MESSAGE.md`).

---

## 16. Conclusion

The AI-Powered Microscopy Analysis System fits the *Software Project Management & Technical Monitoring* course on three counts. First, it has a working software product behind it — a U-Net segmentation pipeline with counting, density heatmaps, and morphology extraction. Second, it carries a realistic target web architecture (FastAPI, React+Vite+TS, PostgreSQL, SQLModel, JWT, Vercel, Railway) that exercises layered design, validation, testing, and deployment. Third, and most importantly for this course, it is wrapped in an explicit management monitoring plan, a technical monitoring plan, a risk register, a stakeholder map, a 4-person role assignment, a 7-minute presentation script, a 3D-inspired design concept, and a final submission checklist. Together, these artefacts demonstrate that the team can plan, build, observe, and deliver a software project under academic time constraints.

---

## 17. References

1. Ronneberger, O., Fischer, P., & Brox, T. (2015). *U-Net: Convolutional Networks for Biomedical Image Segmentation.* In *Medical Image Computing and Computer-Assisted Intervention (MICCAI)*, pp. 234–241.
2. Caicedo, J. C., Roth, J., Goodman, A., Becker, T., Karhohs, K. W., Broisin, M., Csaba, M., McQuin, C., Singh, S., Theis, F. J., & Carpenter, A. E. (2019). *Evaluation of Deep Learning Strategies for Nucleus Segmentation in Fluorescence Images.* *Cytometry Part A*, 95(9), 952–965.
3. Iakubovskii, P. (2019). *Segmentation Models PyTorch.* GitHub repository. https://github.com/qubvel/segmentation_models.pytorch
4. Paszke, A., Gross, S., Massa, F., et al. (2019). *PyTorch: An Imperative Style, High-Performance Deep Learning Library.* In *Advances in Neural Information Processing Systems*, 32.
5. Bradski, G. (2000). *The OpenCV Library.* *Dr. Dobb's Journal of Software Tools.*
6. van der Walt, S., Schönberger, J. L., Nunez-Iglesias, J., et al. (2014). *scikit-image: Image Processing in Python.* *PeerJ*, 2, e453.
7. Tiangolo, S. R. (2018–). *FastAPI Documentation.* https://fastapi.tiangolo.com/
8. Colvin, S. (2017–). *Pydantic Documentation.* https://docs.pydantic.dev/
9. Tiangolo, S. R. (2021–). *SQLModel Documentation.* https://sqlmodel.tiangolo.com/
10. Bayer, M. (2010–). *Alembic Documentation.* https://alembic.sqlalchemy.org/

---

*Document version: v0.3 — 2026-05-03*
