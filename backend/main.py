"""FastAPI entry point for the Nuclei MVP.

Run from the project root::

    uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import Session

from backend.auth.dependencies import get_current_user
from backend.auth.router import router as auth_router
from backend.config import settings
from backend.db import get_session, init_db
from backend.db.models import User
from backend.logging_config import setup_logging
from backend.rate_limit import IPRateLimiter
from backend.schemas import (
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    AnalysisResponse,
    HealthResponse,
)
from backend.services import analysis_service

setup_logging()
log = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
    "image/x-tiff",
}
ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001 (FastAPI lifespan signature)
    """Initialise the database (create tables, seed defaults) on startup."""
    init_db()
    log.info("startup_complete", extra={"event": "startup"})
    yield
    log.info("shutdown_complete", extra={"event": "shutdown"})


app = FastAPI(
    title="Nuclei AI — Microscopy API",
    version="0.3.0",
    description="U-Net nuclei segmentation and counting service.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(auth_router)


@app.middleware("http")
async def request_id_and_timing(request: Request, call_next):
    """Attach a request id, time the request, and emit a structured log line."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        log.info(
            "http_request",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": getattr(response, "status_code", 500),
                "duration_ms": elapsed_ms,
                "client": request.client.host if request.client else None,
            },
        )
        if response is not None:
            response.headers["X-Request-ID"] = rid


RESULT_DIR = settings.result_dir

upload_limiter = IPRateLimiter(
    max_calls=settings.rate_limit_upload_per_minute,
    window_seconds=60,
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**analysis_service.get_health())


def _validate_upload(file: UploadFile) -> None:
    ctype = (file.content_type or "").lower()
    if ctype and ctype not in ALLOWED_IMAGE_TYPES and not ctype.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type: {ctype}. Use PNG, JPEG, TIFF, or BMP.",
        )
    suffix = Path(file.filename or "").suffix.lower()
    if suffix and suffix not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file extension: {suffix}. Use PNG, JPEG, TIFF, or BMP.",
        )


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    upload_limiter.check(request)
    _validate_upload(file)
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Upload exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit."
            ),
        )
    try:
        result = analysis_service.analyze(
            payload,
            file.filename or "upload.png",
            session=session,
            owner_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        log.exception("analysis_failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    return AnalysisResponse(**analysis_service.result_to_dict(result))


@app.get("/api/analyses", response_model=AnalysisHistoryResponse)
def list_analyses(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnalysisHistoryResponse:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200.")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0.")
    payload = analysis_service.list_history(
        session, limit=limit, offset=offset, owner_id=current_user.id, role=current_user.role
    )
    return AnalysisHistoryResponse(
        items=[AnalysisHistoryItem(**item) for item in payload["items"]],
        total=payload["total"],
    )


@app.get("/api/analyses/{job_id}", response_model=AnalysisHistoryItem)
def get_analysis(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AnalysisHistoryItem:
    item = analysis_service.get_history_item(
        session, job_id, owner_id=current_user.id, role=current_user.role
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return AnalysisHistoryItem(**item)


@app.delete("/api/analyses/{job_id}")
def delete_analysis(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from backend.db import repositories

    found = repositories.get_job_with_result(session, job_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    job, _ = found
    if current_user.role != "admin" and job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if not repositories.delete_job(session, job_id):
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"deleted": job_id}


def _file_etag(path: Path) -> str:
    stat = path.stat()
    raw = f"{stat.st_size}-{int(stat.st_mtime)}".encode()
    return hashlib.sha1(raw).hexdigest()


@app.get("/files/{filename}")
def get_file(filename: str, request: Request):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    target = RESULT_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    etag = _file_etag(target)
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})

    return FileResponse(
        target,
        headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=86400, immutable",
        },
    )
