# Final Submission Checklist

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Sign-off rule:** all four members tick their items before the deadline.

> Use this checklist in the final two weeks. Move from weekly to daily review in the last 7 days. M1 owns the final pass.

## A. Compliance & approvals

- [x] **Instructor approval** for the 4-member team is received in writing (see `INSTRUCTOR_APPROVAL_MESSAGE.md`).
- [ ] If approval was granted with conditions, those conditions are reflected in the report and role plan.
- [ ] Role assignment page is final and matches every monitoring/risk/stakeholder owner reference in the package.

## B. Report

- [ ] All 16 sections of `PROJECT_REPORT_DRAFT.md` are filled in.
- [ ] Cover page lists project title, course name, all four student names, IDs, and roles.
- [ ] Every architectural claim is tagged **[Implemented]**, **[Partial]**, or **[Proposed]** — no over-claiming.
- [ ] References / sources used (datasets, libraries, models) are cited in the report.
- [ ] Final report is exported to PDF and re-checked for layout and table rendering.

## C. UI / Dashboard

- [ ] The seven implemented frontend pages (Login, Dashboard, New Analysis, Analysis Result, Analysis History, Reports, Settings) are described in Section 9, with Login labelled visual-demo-only and Reports/Settings labelled MVP placeholders.
- [ ] **Working demo surface** — React + Vite + TS multi-page dashboard (`frontend/`) plus FastAPI backend (`backend/`) with `GET /api/health`, `POST /api/analyze`, and `GET /files/{filename}` — runs end-to-end on a fresh checkout (`npm run build` succeeds; the upload → analyse → result flow returns a real cell count). The Streamlit prototype (`src/app.py`) is retained as a developer-facing reference for the AI core only and is no longer the primary demo surface.
- [ ] Screenshots of the live dashboard (Login, Dashboard, New Analysis with a real result, Analysis History) and of the AI-core outputs (overlay, mask, density heatmap, count, morphology) are inserted into the report and slides.

## D. 3D design concept

- [ ] `UI_3D_DESIGN_CONCEPT.md` is complete (sections A–G).
- [ ] Figma / mockup set exists and is linked in the report and the slides.
- [ ] Implementation status is explicitly stated as **proposed / conceptual** in the report.

## E. Monitoring & risk

- [ ] Management monitoring table (`MANAGEMENT_MONITORING_PLAN.md`) is included in the report and the slides.
- [ ] Technical monitoring table (`TECHNICAL_MONITORING_PLAN.md`) is included in the report and the slides.
- [ ] Risk register (`RISK_MANAGEMENT_PLAN.md`) is included in the report; the 4-vs-6–8 compliance risk is risk #1.
- [ ] Stakeholder table (`STAKEHOLDER_MANAGEMENT_PLAN.md`) is included in the report.

## F. Presentation

- [ ] Slides cover all 12 slides in `PRESENTATION_PLAN_7_MIN.md`.
- [ ] **7-minute timing check.** At least two timed rehearsals; final timing ≤ 7:00.
- [ ] Each presenter has speaker notes; hand-offs are explicit.
- [ ] Slide 9 (3D design concept) explicitly says "proposed design concept."

## G. Backup video

- [ ] Backup presentation video is recorded.
- [ ] Video is uploaded (YouTube / Drive / institutional channel).
- [ ] **Link permission check.** A non-team member opens the link from a logged-out browser and confirms the video plays.
- [ ] Link is included in the report and on a backup slide.

## H. Files & submission

- [ ] Final report file (PDF) name follows the course convention.
- [ ] Slides file (PDF or pptx) follows the course convention.
- [ ] Source-code archive (or repo link) is prepared if the course requires one.
- [ ] All ten files in `docs/` are present and consistent: `PROJECT_REPORT_DRAFT.md`, `ROLE_ASSIGNMENT.md`, `MANAGEMENT_MONITORING_PLAN.md`, `TECHNICAL_MONITORING_PLAN.md`, `RISK_MANAGEMENT_PLAN.md`, `STAKEHOLDER_MANAGEMENT_PLAN.md`, `PRESENTATION_PLAN_7_MIN.md`, `INSTRUCTOR_APPROVAL_MESSAGE.md`, `FINAL_SUBMISSION_CHECKLIST.md`, `UI_3D_DESIGN_CONCEPT.md`.

## I. Deadline

- [ ] **Submitted before the deadline** — not on the hour, not after. Confirm receipt screenshot from the course platform is saved by M1.

## Sign-off

| Member | Role | Sign-off date |
|---|---|---|
| M1 | Project Manager + Risk Manager | _[YYYY-MM-DD]_ |
| M2 | Lead Developer + Backend/API Lead | _[YYYY-MM-DD]_ |
| M3 | AI/ML Engineer + Data Processing Lead | _[YYYY-MM-DD]_ |
| M4 | UX/UI Designer + QA/Testing Lead | _[YYYY-MM-DD]_ |
