# Contributing

Thanks for your interest in Nuclei AI. This guide is short on purpose — it should take
you under 10 minutes to go from a fresh clone to a passing test run.

## Local setup

```bash
# 1. Clone
git clone <repo-url>
cd project

# 2. Python — one-time
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Frontend — one-time
cd frontend
npm install
cd ..

# 4. Configure
cp .env.example .env                      # safe defaults; edit as needed

# 5. Run
uvicorn backend.main:app --reload --port 8000   # backend
cd frontend && npm run dev                       # frontend (separate terminal)
```

The frontend is served at `http://localhost:5173`, the API at `http://127.0.0.1:8000`.
Open the frontend URL — the **Demo Mode** strip on the New Analysis page lets you
exercise the full pipeline without uploading your own image.

## Running the test suite

Backend (pytest):

```bash
pytest -q
```

Frontend (TypeScript):

```bash
cd frontend && npm run typecheck
```

ML pipeline (smoke):

```bash
python -m src.eval_test_set        # runs inference on the test split
python -m src.infer --image path/to/image.png
```

## Code style

- **Python**: Standard PEP 8. `from __future__ import annotations` at the top of
  every module. Google-style docstrings on public functions and classes.
- **TypeScript / React**: Functional components and hooks. JSDoc on exported
  components and API helpers. No default exports for utility modules.
- **Imports**: Group stdlib, third-party, first-party — alphabetised within
  each group.

## Branching and PRs

1. Branch from `main`: `feat/<area>-<short-name>` or `fix/<area>-<short-name>`.
2. Keep PRs scoped — one logical change per PR.
3. Run `pytest` and `npm run typecheck` before pushing.
4. Update `docs/FINAL_REPORT_DRAFT.md` if you change a metric, threshold, or
   architectural element. Reports must match the code.

## Reporting issues

Open a GitHub issue with:

- **Steps to reproduce** — exact commands run.
- **Expected behaviour** — what should have happened.
- **Actual behaviour** — error message, stack trace, screenshot if UI.
- **Environment** — OS, Python version, Node version, GPU/CPU.

## Project structure

| Path | Owns |
|---|---|
| [src/](src/) | ML pipeline — training, inference, evaluation, density maps, morphology |
| [backend/](backend/) | FastAPI service, DB models, repositories, rate limiter, logging |
| [frontend/](frontend/) | React 18 + Vite + Tailwind UI |
| [tests/](tests/) | pytest integration tests for the backend |
| [docs/](docs/) | Final report, SAD, role assignments, plans, design concept |
| [data/](data/) | Train/val/test split CSVs (images are local; not committed) |
| [outputs/](outputs/) | Generated artefacts — checkpoints, masks, overlays, registry |

## Asking for help

- Read [docs/SAD_Phase1.md](docs/SAD_Phase1.md) for architecture context.
- Read [docs/MVP_TO_DEEPLY_ROADMAP.md](docs/MVP_TO_DEEPLY_ROADMAP.md) for phase scope.
- Tag a maintainer in your PR description. Replies within 48h on weekdays.
