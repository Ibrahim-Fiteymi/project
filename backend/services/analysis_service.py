"""Analysis service: wraps the existing U-Net inference + connected-component counter.

Reuses (does not copy):
- src.infer.make_overlay   — overlay rendering
- src.batch_count_refined.count_nuclei_from_binary — counting

If the checkpoint cannot be loaded (missing file, torch error, etc.) the service
falls back to an Otsu-threshold demo path so the UI is still testable end-to-end.
The real AI code in /src is never modified.

When a SQLModel ``Session`` is passed to :func:`analyze`, the service persists
an ``analysis_jobs`` row plus an ``analysis_results`` row so history survives
process restarts and page refreshes. Without a session, the function is still
fully usable for tests and ad-hoc invocations.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from sqlmodel import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.config import settings  # noqa: E402
from backend.db import repositories  # noqa: E402
from src.infer import make_overlay  # noqa: E402
from src.batch_count_refined import count_nuclei_from_binary  # noqa: E402

log = logging.getLogger(__name__)

CHECKPOINT_PATH = settings.checkpoint_path
UPLOAD_DIR = settings.upload_dir
RESULT_DIR = settings.result_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = settings.image_size
THRESHOLD = settings.threshold
MIN_AREA = settings.min_area
MAX_UPLOAD_BYTES = settings.max_upload_bytes

# Lazy singletons populated on first use. The lock guards the first-load race
# under concurrent requests; once `_mode` flips off "uninitialised" we never
# rewrite these globals, so the fast path is lock-free.
_model = None
_device = None
_mode = "uninitialised"  # "model" | "fallback-demo" | "uninitialised"
_load_error: Optional[str] = None
_load_lock = threading.Lock()


@dataclass
class AnalysisResult:
    job_id: str
    status: str
    message: str
    cell_count: int
    input_url: str
    mask_url: str
    overlay_url: str
    metadata: dict


def _ensure_model_loaded() -> None:
    """Load the U-Net checkpoint once. On failure, switch to fallback-demo."""
    global _model, _device, _mode, _load_error
    if _mode != "uninitialised":
        return
    with _load_lock:
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
        except Exception as e:  # noqa: BLE001
            log.exception("model_load_failed")
            _load_error = f"{type(e).__name__}: {e}"
            _mode = "fallback-demo"
            _model = None


def get_health() -> dict:
    _ensure_model_loaded()
    return {
        "status": "ok",
        "device": _device or "cpu",
        "model_loaded": _model is not None,
        "mode": _mode,
        "load_error": _load_error,
    }


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """bytes -> RGB uint8 image resized to IMAGE_SIZE x IMAGE_SIZE."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image. Supported formats: PNG, JPG, TIFF.")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))


def _predict_with_model(image_rgb: np.ndarray) -> np.ndarray:
    """Run U-Net on an RGB uint8 image. Returns binary mask {0,255}."""
    import torch
    tensor = image_rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = torch.tensor(tensor, dtype=torch.float32).unsqueeze(0).to(_device)
    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()
    return ((probs > THRESHOLD).astype(np.uint8)) * 255


def _predict_fallback(image_rgb: np.ndarray) -> np.ndarray:
    """Otsu-threshold demo path. Used only when the real model cannot load."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


def analyze(
    image_bytes: bytes,
    original_filename: str,
    session: Optional[Session] = None,
    *,
    owner_id: Optional[int] = None,
) -> AnalysisResult:
    """Run a full analysis and (optionally) persist a job + result row.

    Args:
        image_bytes: Raw upload payload.
        original_filename: Filename submitted by the client (used for display).
        session: Optional SQLModel session. When provided, a row is written to
            ``analysis_jobs`` before inference and an ``analysis_results`` row
            is written on success. On failure the job is marked ``failed`` and
            the exception is re-raised so the caller can return an HTTP 5xx.

    Returns:
        :class:`AnalysisResult` describing the persisted artefacts.

    Raises:
        ValueError: If the upload exceeds ``MAX_UPLOAD_BYTES`` or cannot be decoded.
    """
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Upload exceeds {MAX_UPLOAD_BYTES} bytes.")

    _ensure_model_loaded()

    job_id = uuid.uuid4().hex[:12]
    suffix = Path(original_filename).suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        suffix = ".png"

    upload_path = UPLOAD_DIR / f"{job_id}{suffix}"
    upload_path.write_bytes(image_bytes)

    parameters_record = {
        "threshold": THRESHOLD,
        "min_area": MIN_AREA,
        "image_size": IMAGE_SIZE,
        "device": _device or "cpu",
        "mode_at_submit": _mode,
    }

    db_job = None
    if session is not None:
        # owner_id falls back to the seeded SYSTEM_USER_ID when called outside
        # an HTTP request (e.g. CLI / tests without auth fixtures).
        from backend.db import SYSTEM_USER_ID
        db_job = repositories.create_job(
            session,
            job_uid=job_id,
            input_path=str(upload_path),
            original_filename=original_filename,
            parameters=parameters_record,
            owner_id=owner_id if owner_id is not None else SYSTEM_USER_ID,
        )

    try:
        image_rgb = _decode_image(image_bytes)

        started = time.perf_counter()
        if _mode == "model":
            mask = _predict_with_model(image_rgb)
            used_min_area = MIN_AREA
        else:
            mask = _predict_fallback(image_rgb)
            used_min_area = 20  # demo path is noisier — drop tiny artefacts
        overlay = make_overlay(image_rgb, mask)
        cell_count = count_nuclei_from_binary(mask, min_area=used_min_area)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        input_path = RESULT_DIR / f"{job_id}_input.png"
        mask_path = RESULT_DIR / f"{job_id}_mask.png"
        overlay_path = RESULT_DIR / f"{job_id}_overlay.png"

        cv2.imwrite(str(input_path), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(mask_path), mask)
        cv2.imwrite(str(overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    except Exception as exc:
        if db_job is not None and session is not None:
            try:
                repositories.fail_job(session, db_job, str(exc))
            except Exception:  # noqa: BLE001
                log.exception("Failed to mark job %s as failed", job_id)
        raise

    if db_job is not None and session is not None:
        repositories.complete_job(
            session,
            db_job,
            cell_count=int(cell_count),
            mode=_mode,
            mask_path=str(mask_path),
            overlay_path=str(overlay_path),
            processing_ms=elapsed_ms,
        )

    status = "ok" if _mode == "model" else "ok-fallback"
    message = (
        "Analysis complete (U-Net inference)."
        if _mode == "model"
        else "Analysis complete (fallback demo mode — model checkpoint not available)."
    )

    return AnalysisResult(
        job_id=job_id,
        status=status,
        message=message,
        cell_count=int(cell_count),
        input_url=f"/files/{input_path.name}",
        mask_url=f"/files/{mask_path.name}",
        overlay_url=f"/files/{overlay_path.name}",
        metadata={
            "original_filename": original_filename,
            "mode": _mode,
            "threshold": THRESHOLD if _mode == "model" else None,
            "min_area": used_min_area,
            "image_size": IMAGE_SIZE,
            "processing_ms": elapsed_ms,
            "device": _device or "cpu",
        },
    )


def _job_to_history_item(job, result) -> dict:
    """Project an (AnalysisJob, AnalysisResult|None) pair to a flat dict."""
    params = job.parameters or {}
    overlay_name = Path(result.overlay_path).name if result and result.overlay_path else None
    mask_name = Path(result.mask_path).name if result and result.mask_path else None
    input_name = Path(job.input_path).name if job.input_path else None
    return {
        "job_id": job.job_uid,
        "status": job.status,
        "cell_count": result.cell_count if result else None,
        "original_filename": job.original_filename,
        "mode": result.mode if result else params.get("mode_at_submit"),
        "processing_ms": result.processing_ms if result else None,
        "input_url": f"/files/{input_name}" if input_name else None,
        "mask_url": f"/files/{mask_name}" if mask_name else None,
        "overlay_url": f"/files/{overlay_name}" if overlay_name else None,
        "threshold": params.get("threshold"),
        "min_area": params.get("min_area"),
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }


def list_history(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    owner_id: Optional[int] = None,
    role: Optional[str] = None,
) -> dict:
    # Admins see everything; everyone else only their own jobs.
    scope_owner = None if role == "admin" else owner_id
    rows = repositories.list_jobs(
        session, limit=limit, offset=offset, owner_id=scope_owner
    )
    items = [_job_to_history_item(job, result) for job, result in rows]
    return {"items": items, "total": len(items)}


def get_history_item(
    session: Session,
    job_uid: str,
    *,
    owner_id: Optional[int] = None,
    role: Optional[str] = None,
) -> Optional[dict]:
    found = repositories.get_job_with_result(session, job_uid)
    if found is None:
        return None
    job, result = found
    if role != "admin" and owner_id is not None and job.owner_id != owner_id:
        return None
    return _job_to_history_item(job, result)


def result_to_dict(r: AnalysisResult) -> dict:
    return asdict(r)
